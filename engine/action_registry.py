from __future__ import annotations

from collections.abc import Callable, Iterable
from importlib import import_module

ActionFn = Callable[..., dict]


class LazyActionRegistry:
    """Resolve action functions only when a flow actually uses them.

    Soporta dos fuentes de registro:

    - Estática: ``register_path('action.name', 'module:callable')``.
    - Dinámica: ``register_callable('action.name', fn)`` (útil para tests
      o paquetes que provean acciones programáticamente).
    - Externa: ``load_entry_points()`` descubre entries ``automa.actions``
      en el entorno (publicadas por terceros vía ``pyproject.toml``).
    """

    def __init__(self, action_paths: dict[str, str]) -> None:
        self._action_paths: dict[str, str] = dict(action_paths)
        self._cache: dict[str, ActionFn] = {}
        self._entry_points_loaded = False

    def get(self, action_name: str) -> ActionFn | None:
        if action_name in self._cache:
            return self._cache[action_name]
        if action_name not in self._action_paths:
            self._maybe_load_entry_points()
            if action_name not in self._action_paths:
                return None
        module_name, function_name = self._action_paths[action_name].split(':', 1)
        module = import_module(module_name)
        fn = getattr(module, function_name)
        self._cache[action_name] = fn
        return fn

    def keys(self) -> Iterable[str]:
        self._maybe_load_entry_points()
        return self._action_paths.keys()

    def register_path(self, action_name: str, dotted_path: str) -> None:
        self._action_paths[action_name] = dotted_path
        self._cache.pop(action_name, None)

    def register_callable(self, action_name: str, fn: ActionFn) -> None:
        # No tenemos un dotted_path real, pero metemos la función directo en cache.
        self._action_paths[action_name] = f'<inline>:{action_name}'
        self._cache[action_name] = fn

    def _maybe_load_entry_points(self) -> None:
        if self._entry_points_loaded:
            return
        self._entry_points_loaded = True
        try:
            from importlib.metadata import entry_points
        except ImportError:  # pragma: no cover - py<3.10 imposible (declared min)
            return
        try:
            eps = entry_points(group='automa.actions')
        except TypeError:
            # Compat py3.9 (no usado, pero por si acaso)
            eps = entry_points().get('automa.actions', [])  # type: ignore[attr-defined]
        for ep in eps:
            self._action_paths.setdefault(ep.name, ep.value)


_BUILT_IN_ACTIONS: dict[str, str] = {
    'filesystem.ensure_directory': 'actions.filesystem:ensure_directory',
    'filesystem.list_directory': 'actions.filesystem:list_directory',
    'filesystem.write_json': 'actions.filesystem:write_json',
    'filesystem.read_text_file': 'actions.filesystem:read_text_file',
    'filesystem.classify_file_inventory': 'actions.filesystem:classify_file_inventory',
    'filesystem.summarize_text_folder': 'actions.filesystem:summarize_text_folder',
    'filesystem.move_file': 'actions.filesystem:move_file',
    'screen.capture_screenshot': 'actions.screen:capture_screenshot',
    'screen.capture_region': 'actions.screen:capture_region',
    'screen.capture_active_window': 'actions.screen:capture_active_window',
    'vision.analyze_image': 'actions.vision:analyze_image',
    'vision.ocr_image': 'actions.vision:ocr_image',
    'vision.find_text_in_image': 'actions.vision:find_text_in_image',
    'vision.select_image': 'actions.vision:select_image',
    'vision.inspect_screen_target': 'actions.vision:inspect_screen_target',
    'system.wait_seconds': 'actions.system:wait_seconds',
    'system.read_clipboard': 'actions.system:read_clipboard',
    'system.snapshot_system': 'actions.system:snapshot_system',
    'system.top_processes': 'actions.system:top_processes',
    'system.watch_processes': 'actions.system:watch_processes',
    'rules.evaluate': 'actions.rules:evaluate_rules',
    'ui.open_url': 'actions.ui:open_url',
    'ui.open_file_in_browser': 'actions.ui:open_file_in_browser',
    'ui.launch_process': 'actions.ui:launch_process',
    'ui.hotkey': 'actions.ui:hotkey',
    'ui.type_text': 'actions.ui:type_text',
    'ui.click': 'actions.ui:click',
    'ui.click_bbox': 'actions.ui:click_bbox',
    'http.fetch_url': 'actions.http_actions:fetch_url',
    'notify.send': 'actions.notify:send_notification',
    'browser.capture_page': 'actions.browser_capture:capture_page',
    'browser.fill_form': 'actions.browser_form:fill_form',
}


ACTION_REGISTRY = LazyActionRegistry(_BUILT_IN_ACTIONS)
