# 17 · Resumen ejecutivo

> Para dirección y para decisión. Sin detalle técnico innecesario. Cada afirmación está
> respaldada por evidencia del repositorio; el detalle está en los documentos que se
> enlazan.

---

## 1. Qué es

**Automa es un producto de automatización de escritorio para Windows.** Convierte tareas
repetitivas —capturar evidencia, rellenar formularios, inventariar carpetas, vigilar
páginas web, auditar el equipo— en recetas escritas que se ejecutan solas, dejando registro
completo de todo lo que hicieron.

Tres decisiones lo definen:

1. **Todo ocurre en el equipo del usuario.** No hay servidor, no hay cuenta, no hay
   telemetría. Con la configuración por defecto, el sistema **no genera tráfico de red**.
2. **No hay inteligencia artificial en el camino de ejecución.** Las decisiones las toman
   reglas escritas por una persona. Verificado: ninguna de las 27 recetas puede alcanzar el
   adaptador de visión con IA que existe en el código.
3. **El sistema crece añadiendo recetas, no modificando el motor.** Las 27 recetas actuales
   están construidas con las 36 operaciones que ya existen.

## 2. Qué necesidad cubre

Un operador que trabaja sobre Windows puede escribir un script para cualquiera de estas
tareas. Lo que no obtiene con un script es lo que Automa aporta:

| Sin Automa | Con Automa |
|---|---|
| Cada script con su propia forma y sus propias reglas | Un contrato único, validado automáticamente |
| Sin registro de qué se ejecutó, cuándo ni con qué resultado | Historial completo, consultable, con duración y evidencia |
| Un script puede escribir donde quiera | Cada receta puede acotar qué acciones usa y dónde escribe |
| Programar la tarea implica salir a otra herramienta | Programador propio, con horarios o intervalos |
| Hay que abrir una terminal | Panel con tarjetas y atajos de teclado |

## 3. Quién lo utiliza

**Un operador local.** No hay usuarios múltiples, ni roles, ni permisos: quien tiene la
sesión de Windows tiene el sistema completo. Es coherente con un producto de escritorio, y
conviene tenerlo presente al evaluar su despliegue.

Perfiles secundarios: quien escribe recetas nuevas (necesita entender un formato JSON, no
programar), quien añade operaciones nuevas (necesita Python) y sistemas externos que
disparan recetas por una llamada autenticada.

## 4. Capacidades principales

**27 casos operativos**, agrupados por lo que hacen:

| Grupo | Casos | Ejemplos |
|---|---:|---|
| Operaciones sobre Windows | 10 | Bloquear la sesión, abrir el Explorador, leer el portapapeles, auditar con PowerShell |
| Extracción y vigilancia web | 9 | Rellenar un formulario, mapear un sitio, detectar cambios en una página, auditar enlaces rotos, extraer tablas |
| Captura de pantalla | 6 | Escritorio limpio, ventana activa, barra de tareas, inventario de texto visible |
| Utilidades sobre archivos | 2 | Inventario de carpeta, resumen de documentos de texto |

Más: panel de tres pestañas con atajos de teclado, programador con horarios tipo cron,
métricas en formato estándar de la industria, instalador de Windows que no requiere
permisos de administrador, y un mecanismo para que terceros publiquen operaciones nuevas.

## 5. Tecnologías

Python 3.10 o superior, sin framework web ni base de datos externa. SQLite para el
historial. El navegador Chromium se controla con Playwright cuando una receta lo necesita.
El instalador se construye con PyInstaller e Inno Setup. Licencia MIT.

**Dependencias externas relevantes:** nueve paquetes declarados, todos con versión mínima
elegida por criterio de seguridad y con motivo escrito en el propio código.

## 6. Arquitectura resumida

Un archivo JSON describe la tarea. Un motor lo lee, comprueba los permisos que la propia
receta declara, ejecuta cada paso y guarda todo lo que pasó en tres sitios a la vez: base
de datos, registro de eventos y copia completa del estado. El panel y el programador de
horarios son dos formas de disparar ese mismo motor.

Es deliberadamente **un solo proceso, sin servicios ni colas**. Para una herramienta local
de un operador, es la decisión correcta.

## 7. Estado actual verificado

Medido ejecutando los propios controles del proyecto sobre el código publicado
(commit `ff246ab`, versión `0.3.0`):

| Control | Resultado |
|---|---|
| Suite de pruebas | **150 de 150 pasan** |
| Cobertura de código | **59 %** (umbral exigido: 54 %) |
| Análisis de estilo | **Sin hallazgos** |
| Validación de las 27 recetas | **Sin errores** |
| Prueba de humo de extremo a extremo | **Correcta** |
| Estado del repositorio | Limpio |

**Los cuatro controles del proyecto están en verde.**

Tamaño: 210 archivos, 6 126 líneas de código de producción y 1 525 de pruebas. Es un
proyecto pequeño y manejable.

## 8. Fortalezas

Cinco propiedades destacan por encima de la media de proyectos de este tamaño:

1. **Seguridad de la cadena de suministro tratada como problema de primer orden.** Doce
   capas de defensa en el pipeline, incluyendo un verificador propio que impide introducir
   una dependencia sin fijar, y un escaneo de credenciales sobre los últimos cincuenta
   cambios del historial. El razonamiento está escrito en el propio código: este producto
   puede controlar el teclado del usuario, así que un cambio malicioso equivale a control
   del equipo.

2. **El sistema nunca oculta lo que no hizo.** Cuando recorta un resultado, lo declara.
   Cuando falta un componente externo, devuelve un mensaje con las instrucciones de
   instalación en vez de fallar de forma opaca. Es una disciplina poco común y muy valiosa
   para la confianza del operador.

3. **Diseño que hace testeable lo que normalmente no lo es.** La familia de recetas web
   alcanza **91 % de cobertura sin abrir un solo navegador**, porque la lógica está separada
   de la interacción. Las operaciones que mueven teclado y ratón tienen un modo de ensayo.

4. **Las decisiones están documentadas donde importan.** Los comentarios del código
   explican *por qué* existe cada control y qué tipo de fallo cierra, no qué hace la línea
   siguiente. Esto reduce drásticamente el costo de auditar y de incorporar gente nueva.

5. **Crece por casos, no por refactor.** Añadir una funcionalidad es añadir una carpeta con
   un JSON. El motor lleva tres versiones sin necesitar cambios estructurales.

## 9. Riesgos

Se identificaron **27 hallazgos**: 6 de severidad alta, 12 media y 9 baja. Detalle completo
en [15 · Riesgos y deuda técnica](15-risks-and-technical-debt.md). Los cuatro que exigen
decisión:

| # | Riesgo | Consecuencia | Esfuerzo de corrección |
|---|---|---|---|
| 1 | **Siete recetas probablemente no funcionan en el producto instalado** | La familia web completa —la novedad de la última versión— fallaría en el instalador que descarga el usuario final. Falta declarar un módulo en la configuración de empaquetado | **< 1 hora** |
| 2 | **El historial completo es legible sin autenticación** | Capturas de pantalla, contenido del portapapeles y texto de ventanas abiertas quedan accesibles desde la interfaz local sin clave, incluso teniendo una configurada. En un equipo de un solo usuario el riesgo es bajo; deja de serlo si se comparte el equipo o se expone el panel | **< 1 hora** |
| 3 | **La mitad de las recetas corre sin restricciones declaradas** | 14 de 27 no acotan qué pueden hacer ni dónde escribir. Nada en el proceso automático lo exige, así que el hueco crece con cada caso nuevo | **1 hora** el control automático; días retroadaptar las 14 |
| 4 | **La línea de comandos falla en Windows** | Los comandos `automa list` y `automa run` terminan con error al mostrar el resultado. La tarea sí se ejecuta correctamente; lo que falla es la impresión posterior. Se soluciona con una variable de entorno | **< 1 hora** |

**Riesgos de operación a medio plazo:** no existe ninguna rutina de limpieza del historial,
que crece sin límite; y una tarea programada que falle de forma sistemática no genera
ninguna alerta.

## 10. Oportunidades de mejora

Ordenadas por relación entre esfuerzo y beneficio:

| Prioridad | Acción | Esfuerzo | Beneficio |
|---|---|---|---|
| 1 | Corregir el empaquetado de la familia web | < 1 h | Recupera 7 de 27 casos en el producto distribuido |
| 2 | Exigir autenticación también en las consultas | < 1 h | Cierra la exposición del historial |
| 3 | Que el validador exija restricciones en toda receta nueva | 1 h | Impide que el problema crezca |
| 4 | Arreglar la salida de la línea de comandos | < 1 h | Elimina un fallo visible |
| 5 | Sincronizar los tres listados de dependencias que hoy difieren | 1 h | Instalaciones reproducibles |
| 6 | Añadir índices a la base de datos y una rutina de limpieza | 1 día | Sostenibilidad a largo plazo |
| 7 | Aviso ante tareas programadas que fallan de forma repetida | 1 día | Operación desatendida fiable |
| 8 | Pruebas de las tres partes hoy sin cubrir | 2 días | Reduce el riesgo de regresión |

**Total de las cinco primeras: menos de un día de trabajo**, y resuelven los cuatro riesgos
altos.

## 11. Estado de madurez, con honestidad

| Dimensión | Valoración | Fundamento |
|---|---|---|
| Motor y arquitectura | **Sólido** | 87 % de cobertura en el componente central; tres versiones sin cambios estructurales |
| Catálogo de casos | **Sólido** | 27 casos validados automáticamente |
| Pruebas de la lógica pura | **Sólido** | 150 pruebas, ejecución en 17 segundos |
| Seguridad del proceso de construcción | **Muy sólido** | Por encima de la media del sector |
| Interfaz de usuario | **Funcional** | Cubre lo necesario; el 62 % de su código no tiene pruebas |
| Empaquetado y distribución | **Con un fallo pendiente** | Automatizado, pero con el riesgo nº 1 abierto |
| Seguridad en ejecución | **Parcial** | Las restricciones existen, funcionan y la mitad del catálogo no las usa |
| Operación desatendida | **Incompleta** | Sin alertas, sin limpieza, sin recuperación automática |
| Documentación | **Buena y ahora completa** | Doce documentos previos orientados a producto, más estos veinte de sistema |

**Lectura de conjunto:** el sustrato está bien construido y bien probado. Los huecos están
donde el sistema toca el mundo real —interfaz, empaquetado, operación continua— y todos son
conocidos, están localizados y son abordables.

## 12. Próximos pasos recomendados

### Inmediato — antes de la siguiente publicación

Los cuatro riesgos altos con corrección de menos de una hora cada uno: el empaquetado de la
familia web, la autenticación de las consultas, el fallo de la línea de comandos y la
sincronización de los listados de dependencias. **Menos de un día en total.**

### Corto plazo — próximas semanas

- Regla automática que exija restricciones de seguridad en toda receta nueva.
- Índices en la base de datos y rutina de limpieza configurable.
- Pruebas de las tres partes hoy sin cubrir.
- Documentar las tres particularidades del programador de horarios que hoy son silenciosas
  y pueden hacer que una tarea se ejecute el día o la hora equivocados.

### Medio plazo — decisiones de dirección

Cuatro puntos que requieren una decisión, no solo trabajo técnico:

1. **Qué hacer con el adaptador de inteligencia artificial.** Son 222 líneas capaces de
   enviar capturas de pantalla a un servicio externo, sin ninguna receta que las use.
   Contradice aparentemente el posicionamiento del producto, aunque en la práctica sea
   inalcanzable. Opciones: eliminarlo, documentarlo explícitamente como punto de extensión,
   o construir el caso que lo justifique.
2. **Si el producto debe operar desatendido.** Si la respuesta es sí, faltan alertas,
   limpieza automática y recuperación de tareas colgadas.
3. **Si el equipo puede ser compartido.** Si la respuesta es sí, hace falta cifrado del
   historial y de las capturas, que hoy quedan en claro y sobreviven a la desinstalación.
4. **Si conviene firmar el instalador.** Hoy sin firma, lo que provoca un aviso de Windows
   al instalar y afecta a la percepción de confianza.

### Lo que no hace falta hacer

- **No hace falta refactorizar el motor.** Funciona, está probado y su diseño ha soportado
  tres versiones de crecimiento.
- **No hace falta cambiar de base de datos.** SQLite es adecuado; lo que falta son índices
  y limpieza.
- **No hace falta añadir inteligencia artificial.** El determinismo es una característica
  del producto, no una carencia.

---

## 13. Una frase para llevarse

> **Automa es un producto pequeño, bien construido y honesto sobre sus límites, con cuatro
> problemas concretos que se corrigen en menos de un día y que hoy afectan a un tercio de
> su catálogo en el producto que descarga el usuario final.**

---

**Documentos relacionados:**
[01 · Descripción general](01-system-overview.md) ·
[11 · Seguridad](11-security.md) ·
[12 · Pruebas y calidad](12-testing-and-quality.md) ·
[15 · Riesgos y deuda técnica](15-risks-and-technical-debt.md) ·
[16 · Glosario](16-glossary.md)
