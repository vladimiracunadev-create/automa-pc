"""Motor de ejecución: convierte un manifest declarativo en una corrida trazable.

Es el único módulo que conoce a la vez el contrato del flow, la política de
sandbox, el registro de acciones y los tres almacenes de persistencia. Todo lo
demás del sistema es o bien una fuente de disparo (panel, CLI, scheduler,
webhook) o bien una pieza que este bucle usa.

Orden de los controles antes de cada paso, y **el orden importa**:

1. ``assert_secrets_present`` — una sola vez, al arrancar la corrida.
2. ``assert_action_allowed`` — barato, va antes de renderizar.
3. ``render_value`` sobre los ``params``.
4. ``assert_paths_allowed`` — **después** de renderizar: un placeholder sin
   resolver no se puede validar como ruta.
5. Comprobación de ``max_runtime_seconds``.

Advertencias para quien modifique este archivo:

* ``max_runtime_seconds`` se comprueba **entre** pasos. Una acción que se cuelga
  dentro no se interrumpe: es un control de arranque de paso, no un timeout.
* ``render_value`` se llama **una vez por paso**, fuera del bucle de reintentos.
  Un ``{now}`` en un nombre de archivo no cambia entre intentos, y eso es
  intencional.
* La recuperación ante fallo se detecta comparando el destino de la transición
  ``on: "failure"`` con ``_default_next``. Si coinciden, el motor NO lo considera
  rama de recuperación y la corrida se marca ``failed``.
* ``self.state['context']`` es **la misma referencia** que ``self.context``, no
  una copia. El snapshot persistido refleja siempre el contexto vivo, a cambio de
  que todo él acabe en la columna ``context_json`` de la tabla ``runs``.
* ``_persist()`` se llama tras **cada** paso: recorre el estado buscando outputs,
  reescribe el JSON completo y hace un upsert en SQLite. Barato para flows
  cortos, caro para flows largos con contexto grande.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engine.action_registry import ACTION_REGISTRY
from engine.conditions import evaluate_condition
from engine.database import init_db, insert_step, upsert_run
from engine.introspection import extract_existing_paths
from engine.loader import FlowLoader
from engine.logger import JsonlLogger
from engine.paths import data_dir
from engine.sandbox import SandboxPolicy, SandboxViolation
from engine.state_store import StateStore
from engine.template import render_value


class FlowExecutionError(Exception):
    pass


class Orchestrator:
    def __init__(
        self,
        flow_dir: Path,
        context_path: Path | None = None,
        context_overrides: dict[str, Any] | None = None,
    ) -> None:
        init_db()
        self.flow_dir = flow_dir
        self.definition = FlowLoader.load_manifest(flow_dir)
        self.context = FlowLoader.load_context(flow_dir, context_path)
        if context_overrides:
            self.context = {**self.context, **context_overrides}
        self.policy = SandboxPolicy(
            allowed_actions=self.definition.allowed_actions,
            required_secrets=self.definition.required_secrets,
            allowed_paths=self.definition.allowed_paths,
            max_runtime_seconds=self.definition.max_runtime_seconds,
        )
        self.run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        _data = data_dir()
        self.log_path = _data / 'logs' / f'{self.definition.id}_{self.run_id}.jsonl'
        self.state_path = _data / 'state' / f'{self.definition.id}_{self.run_id}.json'
        self.logger = JsonlLogger(self.log_path, run_id=self.run_id)
        self.state_store = StateStore(self.state_path)
        self.steps_by_id = {step.id: step for step in self.definition.steps}
        self.step_order = [step.id for step in self.definition.steps]
        self.state: dict[str, Any] = {
            'flow_id': self.definition.id,
            'flow_name': self.definition.name,
            'description': self.definition.description,
            'family': self.definition.family,
            'run_id': self.run_id,
            'flow_dir': str(self.flow_dir),
            'status': 'created',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'started_at': None,
            'finished_at': None,
            'duration_seconds': None,
            'steps': [],
            'context': self.context,
            'outputs': [],
            'error': None,
            'route': [],
        }

    def _refresh_outputs(self) -> None:
        self.state['outputs'] = extract_existing_paths(self.state)

    def _persist(self) -> None:
        self._refresh_outputs()
        self.state_store.save(self.state)
        upsert_run(self.state, self.flow_dir.name, str(self.state_path), str(self.log_path))

    def _default_next(self, current_step_id: str) -> str | None:
        try:
            index = self.step_order.index(current_step_id)
        except ValueError:
            return None
        next_index = index + 1
        if next_index >= len(self.step_order):
            return None
        return self.step_order[next_index]

    def _resolve_transition(self, step, event: str) -> str | None:
        for transition in step.transitions:
            if transition.on not in {event, 'any'}:
                continue
            if transition.when and not evaluate_condition(transition.when, self.context):
                continue
            if transition.end:
                return '__END__'
            if transition.next_step:
                return transition.next_step
        return self._default_next(step.id)

    def run(self) -> dict[str, Any]:
        started_at = datetime.now(timezone.utc)
        try:
            self.policy.assert_secrets_present()
        except SandboxViolation as exc:
            self.state['status'] = 'failed'
            self.state['error'] = {'message': str(exc), 'kind': 'sandbox_violation'}
            self._persist()
            self.logger.write('flow_blocked', {'reason': str(exc)})
            raise FlowExecutionError(str(exc)) from exc
        self.state['status'] = 'running'
        self.state['started_at'] = started_at.isoformat()
        self.state['policy'] = self.policy.summary()
        self._persist()
        self.logger.write(
            'flow_started',
            {'flow_id': self.definition.id, 'run_id': self.run_id, 'policy': self.policy.summary()},
        )

        current_step_id = self.definition.start_step or (self.step_order[0] if self.step_order else None)
        executed_count = 0

        try:
            while current_step_id:
                if executed_count >= self.definition.max_steps_per_run:
                    raise FlowExecutionError('Se alcanzó el máximo de pasos permitidos para esta corrida.')
                if current_step_id == '__END__':
                    break
                step = self.steps_by_id.get(current_step_id)
                if step is None:
                    raise FlowExecutionError(f'Paso no encontrado: {current_step_id}')

                self.state['route'].append(current_step_id)

                if step.when and not evaluate_condition(step.when, self.context):
                    step_record = {
                        'step_id': step.id,
                        'action': step.action,
                        'attempt': 0,
                        'status': 'skipped',
                        'params': step.params,
                        'result': {'reason': 'condition_not_met'},
                        'started_at': datetime.now(timezone.utc).isoformat(),
                        'finished_at': datetime.now(timezone.utc).isoformat(),
                        'duration_seconds': 0.0,
                    }
                    self.state['steps'].append(step_record)
                    insert_step(self.run_id, len(self.state['steps']), step_record)
                    self.logger.write('step_skipped', {'step_id': step.id, 'reason': 'condition_not_met'})
                    self._persist()
                    current_step_id = self._resolve_transition(step, event='success')
                    executed_count += 1
                    continue

                try:
                    self.policy.assert_action_allowed(step.action)
                except SandboxViolation as exc:
                    self.state['status'] = 'failed'
                    self.state['error'] = {'step_id': step.id, 'message': str(exc), 'kind': 'sandbox_violation'}
                    self._persist()
                    self.logger.write('step_blocked', {'step_id': step.id, 'reason': str(exc)})
                    raise FlowExecutionError(str(exc)) from exc
                rendered_params = render_value(step.params, self.context)
                try:
                    self.policy.assert_paths_allowed(rendered_params)
                except SandboxViolation as exc:
                    self.state['status'] = 'failed'
                    self.state['error'] = {'step_id': step.id, 'message': str(exc), 'kind': 'sandbox_violation'}
                    self._persist()
                    self.logger.write('step_blocked', {'step_id': step.id, 'reason': str(exc)})
                    raise FlowExecutionError(str(exc)) from exc
                action = ACTION_REGISTRY.get(step.action)
                if action is None:
                    raise FlowExecutionError(f'Acción no registrada: {step.action}')
                if self.policy.max_runtime_seconds is not None:
                    elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()
                    if elapsed > self.policy.max_runtime_seconds:
                        raise FlowExecutionError(
                            f'Se superó max_runtime_seconds={self.policy.max_runtime_seconds}s'
                        )

                attempts = 0
                while attempts <= step.retries:
                    attempts += 1
                    step_started_at = datetime.now(timezone.utc)
                    try:
                        self.logger.write(
                            'step_started',
                            {'step_id': step.id, 'action': step.action, 'attempt': attempts, 'params': rendered_params},
                        )
                        result = action(**rendered_params)
                        self.context['_last_result'] = result
                        if step.save_as:
                            self.context[step.save_as] = result
                        self.state['context'] = self.context
                        finished = datetime.now(timezone.utc)
                        step_record = {
                            'step_id': step.id,
                            'action': step.action,
                            'attempt': attempts,
                            'status': 'success',
                            'params': rendered_params,
                            'result': result,
                            'started_at': step_started_at.isoformat(),
                            'finished_at': finished.isoformat(),
                            'duration_seconds': round((finished - step_started_at).total_seconds(), 4),
                        }
                        self.state['steps'].append(step_record)
                        insert_step(self.run_id, len(self.state['steps']), step_record)
                        self._persist()
                        self.logger.write('step_finished', {'step_id': step.id, 'status': 'success', 'result': result})
                        current_step_id = self._resolve_transition(step, event='success')
                        break
                    except Exception as exc:  # noqa: BLE001
                        last_error = str(exc)
                        self.context['_last_error'] = {'message': last_error, 'step_id': step.id}
                        self.logger.write('step_failed', {'step_id': step.id, 'attempt': attempts, 'error': last_error})
                        if attempts > step.retries:
                            finished = datetime.now(timezone.utc)
                            step_record = {
                                'step_id': step.id,
                                'action': step.action,
                                'attempt': attempts,
                                'status': 'failed',
                                'params': rendered_params,
                                'error': last_error,
                                'started_at': step_started_at.isoformat(),
                                'finished_at': finished.isoformat(),
                                'duration_seconds': round((finished - step_started_at).total_seconds(), 4),
                            }
                            self.state['steps'].append(step_record)
                            insert_step(self.run_id, len(self.state['steps']), step_record)
                            recovery_next = self._resolve_transition(step, event='failure')
                            if recovery_next and recovery_next != self._default_next(step.id):
                                self.logger.write('step_recovered', {'step_id': step.id, 'next': recovery_next, 'error': last_error})
                                current_step_id = recovery_next
                                self._persist()
                                break
                            self.state['status'] = 'failed'
                            self.state['error'] = {'step_id': step.id, 'message': last_error}
                            self._persist()
                            raise FlowExecutionError(
                                f"Falló el paso '{step.id}' tras {attempts} intento(s): {last_error}"
                            ) from exc
                executed_count += 1
                if self.state['status'] == 'failed':
                    break
        except Exception:
            finished_at = datetime.now(timezone.utc)
            self.state['finished_at'] = finished_at.isoformat()
            self.state['duration_seconds'] = round((finished_at - started_at).total_seconds(), 4)
            self._persist()
            self.logger.write(
                'flow_finished',
                {'flow_id': self.definition.id, 'run_id': self.run_id, 'status': self.state['status'], 'error': self.state['error']},
            )
            raise

        finished_at = datetime.now(timezone.utc)
        self.state['status'] = 'completed'
        self.state['finished_at'] = finished_at.isoformat()
        self.state['duration_seconds'] = round((finished_at - started_at).total_seconds(), 4)
        self._persist()
        self.logger.write('flow_finished', {'flow_id': self.definition.id, 'run_id': self.run_id, 'status': self.state['status']})
        return self.state
