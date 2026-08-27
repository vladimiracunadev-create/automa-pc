# 16 · Glosario

> Términos técnicos, siglas y palabras del dominio, explicados para que los entienda
> alguien sin formación técnica. Los términos marcados **🔷 propio de Automa** significan
> algo específico **en este sistema** y no coinciden necesariamente con su uso general.

---

## A

**Acción** · 🔷 propio de Automa
Una operación concreta que el sistema sabe hacer: sacar una foto de la pantalla, escribir
un archivo, abrir el Explorador, leer una página web. Hay **36**. Cada una tiene un nombre
con punto (`screen.capture_screenshot`) y un flow la invoca escribiendo ese nombre en su
receta. *Analogía:* son los verbos del idioma en que se escriben las recetas.

**allowed_actions** · 🔷 propio de Automa
Lista escrita dentro de una receta que dice qué acciones puede usar. Si una receta la
declara, el motor rechaza cualquier acción que no esté en la lista. **Es opcional, y 14 de
las 27 recetas actuales no la tienen.**
> ⚠️ Escribir una lista **vacía** no bloquea nada: el sistema la interpreta como «sin
> restricción». Ver [15 · Riesgos](15-risks-and-technical-debt.md), hallazgo R-05.

**allowed_paths** · 🔷 propio de Automa
Lista de carpetas donde una receta puede leer o escribir. El motor comprueba las rutas
antes de cada paso. *Detalle importante:* la comprobación se hace mirando **el nombre del
parámetro**, no su contenido; un parámetro llamado `target` que contenga una ruta no se
revisa.

**Analizador** · 🔷 propio de Automa
Componente intercambiable que examina una imagen. Hay cuatro: `mock` (mide el brillo
medio), `metadata` (dimensiones y huella digital), `ocr` (lee el texto de la imagen) y uno
de visión con inteligencia artificial que **ningún caso del sistema utiliza**.

**API** · *Application Programming Interface*
La forma en que otro programa puede hablar con este. Automa ofrece una API en
`127.0.0.1:8787`: un programa puede pedirle que ejecute una receta o consultar el
historial.

**Append-only**
Un archivo al que solo se añaden líneas al final; nada se reescribe ni se borra. Los
registros de eventos de Automa (`logs/*.jsonl`) funcionan así. *Analogía:* un cuaderno en
el que solo se escribe hacia adelante.

## B

**Bbox** · abreviatura de *bounding box*, «caja delimitadora»
Un rectángulo definido por cuatro números: dónde empieza a la izquierda, dónde empieza
arriba, cuánto mide de ancho y cuánto de alto. Se usa para recortar una parte de la
pantalla o para señalar dónde está una palabra dentro de una imagen.
> En Automa, un valor **negativo** significa «contado desde el borde opuesto». Por eso la
> barra de tareas se captura con `top: -48`: cuarenta y ocho puntos desde abajo.

**BFS** · *Breadth-First Search*, recorrido en anchura
Forma de explorar un sitio web: primero se visitan todas las páginas enlazadas desde la
principal, después las enlazadas desde aquellas, y así sucesivamente. Automa lo usa para
hacer el mapa de un sitio, siempre con un tope de páginas y de profundidad.

## C

**Caso / Flow / Flujo** · 🔷 propio de Automa
Una receta. Una carpeta dentro de `flows/` con tres archivos: la receta en sí
(`manifest.json`), sus valores por defecto (`context.example.json`) y su explicación
(`README.md`). Hay **27**.

**Chromium**
El navegador que Automa arranca por su cuenta para ver páginas web. Es el mismo motor que
usan Chrome y Edge. Automa lo controla con una biblioteca llamada Playwright. **Hay que
instalarlo aparte**: no viene con el programa.

**CI / CD** · *Continuous Integration / Continuous Delivery*
Los robots que revisan el código automáticamente cada vez que alguien lo modifica, y los
que construyen el instalador cuando llega el momento de publicar una versión. Automa tiene
seis de estos robots configurados.

**Contexto** · 🔷 propio de Automa
El cuaderno de notas de una ejecución. Empieza con los valores de configuración de la
receta, y cada paso puede añadirle su resultado. El paso siguiente puede leer lo que
escribió el anterior. Al terminar, todo el cuaderno se guarda en el historial.

**Cron**
Una forma abreviada y muy antigua de escribir horarios: cinco números separados por
espacios que significan minuto, hora, día del mes, mes y día de la semana. `*/15 * * * *`
significa «cada quince minutos».
> ⚠️ **En Automa, `0` es lunes**, mientras que en el estándar de toda la vida `0` es
> domingo. Y las horas se cuentan en UTC, no en la hora local. Una expresión copiada de
> internet se ejecutará el día o la hora equivocados sin dar ningún error.

**CSRF** · *Cross-Site Request Forgery*
Un ataque en el que una página web maliciosa que usted visita intenta dar órdenes a un
programa que corre en su propio computador, aprovechando que su navegador ya está «dentro».
Automa se defiende comprobando de dónde viene cada orden.

**CVE** · *Common Vulnerabilities and Exposures*
El catálogo público mundial de fallos de seguridad conocidos. Cada fallo tiene un número.
Automa fija versiones mínimas de sus componentes eligiendo la primera versión sin fallos
conocidos.

**CWE** · *Common Weakness Enumeration*
Catálogo de **tipos** de fallo de seguridad, no de fallos concretos. Por ejemplo, CWE-78 es
«inyección de comandos». Los comentarios del código de Automa citan qué CWE cierra cada
control, lo que facilita mucho auditarlo.

## D

**Determinista** · 🔷 clave en este sistema
Que hace exactamente lo mismo cada vez que se ejecuta, sin sorpresas ni improvisación.
**Es la propiedad central de Automa**: no hay inteligencia artificial decidiendo nada. La
única excepción intencional es el caso 07, que elige un registro al azar entre los que aún
no ha usado.

**Degradación (elegante)** · 🔷 patrón de Automa
Cuando falta algo que un componente necesita, en vez de reventar, avisa con claridad y
devuelve un resultado vacío pero válido. Si falta el lector de texto en imágenes, el
sistema responde «no disponible, instálalo así» y la receta puede seguir por otro camino.

**Dry run** · «ensayo en seco» · 🔷 propio de Automa
Modo de prueba de las recetas que mueven el teclado o el ratón. Con `dry_run` activado, el
sistema dice qué **habría** hecho, sin hacerlo. Es la forma segura de probar una receta
nueva.

## E

**Entry point** · «punto de entrada»
Dos significados distintos:
1. **El comando que arranca el programa**: `automa`, `automa-panel`, `automa-desktop`.
2. **El mecanismo por el que otro programa puede añadir acciones nuevas** a Automa sin
   tocar su código.
> Una acción de un tercero **nunca puede reemplazar** a una interna: el sistema da
> prioridad a las suyas.

**Evento** · 🔷 propio de Automa
Cada cosa que pasa durante una ejecución queda anotada como un evento: la receta empezó,
un paso arrancó, un paso falló, la receta terminó. Hay nueve tipos. Se guardan **dos
veces**: en un archivo y en la base de datos.

## F

**Familia** · 🔷 propio de Automa
Etiqueta que agrupa las recetas por lo que hacen. Hay cinco: `sistema` (10 recetas),
`navegador` (9), `pantalla` (6), `filesystem` (1) y `documentos` (1).

**Frozen** · «congelado»
Se dice del programa cuando se ha empaquetado en un único ejecutable, en vez de ejecutarse
desde el código fuente. Automa se comporta distinto en ese modo: guarda sus datos en otra
carpeta, porque la del programa es de solo lectura.

## H

**Hash / SHA-256** · «huella digital»
Un número largo que resume un texto o un archivo. Si el contenido cambia aunque sea en una
letra, la huella cambia por completo. Automa lo usa para saber si una página web cambió
desde la última vez, sin tener que guardar la página entera.

**Headless** · «sin cabeza»
Un navegador que funciona sin mostrar ventana. Automa lo usa para leer páginas web sin
molestar al usuario. La única receta que **sí** muestra ventana es la 07, y lo hace a
propósito: es la demostración del producto.

## L

**Local-first** · «primero local» · 🔷 filosofía del producto
Todo ocurre en su computador. No hay servidor en internet, no hay cuenta de usuario, no se
envía nada a ningún sitio. El programa escucha únicamente en la dirección `127.0.0.1`, que
significa «este mismo equipo».

**Lock** · «cerrojo» · 🔷 propio de Automa
Marca que impide que la misma receta se ejecute dos veces a la vez.
> ⚠️ **Solo lo usa el programador de horarios.** Lanzar la misma receta dos veces desde el
> panel sí es posible.

**LLM** · *Large Language Model*, modelo de lenguaje grande
Lo que popularmente se llama «una inteligencia artificial que escribe». **Automa no usa
ninguno.** Existe en el código un adaptador capaz de hablar con uno, pero ninguna de las 27
recetas puede llegar hasta él.

## M

**Manifest** · «manifiesto» · 🔷 propio de Automa
El archivo `manifest.json` de una receta: la receta escrita. Dice qué pasos hay, en qué
orden, con qué valores y qué hacer si algo falla. *Es el corazón del sistema*: añadir una
funcionalidad nueva es escribir uno de estos, no programar.

**Mermaid**
Un lenguaje para dibujar diagramas escribiendo texto. Los diagramas de esta documentación
están escritos así, y se convierten en imágenes al generar los PDF.

## O

**OCR** · *Optical Character Recognition*, reconocimiento óptico de caracteres
Leer el texto que aparece dentro de una imagen. Automa lo usa para inventariar lo que se ve
en el escritorio. Necesita un programa externo llamado `tesseract`; si falta, Automa lo
dice con claridad en vez de fallar.

**Orquestador** · 🔷 propio de Automa
El motor que lee la receta y la ejecuta paso a paso, comprobando permisos, sustituyendo
valores y anotándolo todo. Vive en `engine/orchestrator.py`.

## P

**Panel**
La pantalla desde la que se maneja todo. Tiene tres pestañas: **Ejecutar** (una tarjeta por
receta), **Programadas** (horarios) e **Histórico** (todo lo que se ha ejecutado).

**Paso** · *step* · 🔷 propio de Automa
Cada instrucción de una receta. Tiene un nombre, la acción que ejecuta, sus valores, cuántas
veces reintentar si falla y una condición opcional para saltárselo.

**Placeholder** · «marcador de posición» · 🔷 propio de Automa
Un hueco en la receta que se rellena al ejecutarla. Se escribe entre llaves:
`{{ target_url }}` se sustituye por la dirección configurada, y `{now}` por la fecha y hora
del momento.

**Playwright**
La biblioteca que permite a Automa controlar el navegador Chromium: abrirlo, navegar,
rellenar formularios y leer el contenido. **No se instala automáticamente.**

**Preview** · 🔷 propio de Automa
Marca que señala una receta como «todavía no lista». El panel la muestra con un aviso y
bloquea su ejecución. **Ninguna de las 27 recetas actuales está marcada así.**

**Prometheus**
Un formato estándar para publicar números de funcionamiento (cuántas ejecuciones, cuánto
tardaron, cuántas fallaron) que otros programas de vigilancia saben leer.

**pywebview**
La biblioteca que mete el panel dentro de una ventana normal de Windows, para que no haya
que abrir un navegador.

## R

**Regla** · *rule* · 🔷 propio de Automa
Una comprobación escrita dentro de la receta: «si la memoria supera el 80 %, marca esto
como alerta». Se evalúan en orden y **gana la primera que se cumple**.
> Las reglas soportan 6 comparadores, mientras que las condiciones de los pasos soportan
> 13. No son el mismo motor.

**Reintento** · *retry*
Cuántas veces volver a intentar un paso que falló. Por defecto, ninguna.
> ⚠️ **No hay espera entre reintentos.** Tres intentos contra un servidor caído ocurren en
> milisegundos.

**robots.txt**
Un archivo que los sitios web publican para indicar qué pueden y qué no pueden visitar los
programas automáticos. Automa lo respeta al recorrer un sitio. Si no lo puede leer, permite
el acceso **pero lo deja anotado** en el informe.

**Run / Corrida** · 🔷 propio de Automa
Una ejecución concreta de una receta, con su identificador único, su hora de inicio, su
duración y su resultado. Todo queda en el historial.

## S

**Sandbox** · «caja de arena» · 🔷 propio de Automa
Las restricciones que una receta se impone a sí misma: qué acciones puede usar, dónde
puede escribir y cuánto puede tardar.
> ⚠️ **Es una promesa, no una jaula.** Las hace cumplir el propio programa, no el sistema
> operativo. *Analogía:* es un cartel de «no pasar», no una puerta cerrada con llave. Y
> catorce de las veintisiete recetas no llevan cartel puesto.

**Scheduler** · «programador de tareas» · 🔷 propio de Automa
El componente que revisa cada dos segundos si toca ejecutar alguna receta programada.
> ⚠️ **Si una receta programada falla, no avisa a nadie.** Reprograma la siguiente
> ejecución con normalidad. Solo se descubre mirando el historial.

**Secreto** · *secret*
Una contraseña, clave o testigo de acceso. Automa los busca primero en las variables del
sistema y después en un archivo. **Ese archivo no está cifrado**: lo protegen únicamente
los permisos del sistema operativo.

**SQLite**
Una base de datos que cabe en un solo archivo (`db/runs.db`) y no necesita ningún servicio
corriendo aparte. Es donde vive todo el historial de Automa.

**Supply chain** · «cadena de suministro»
Todo lo que entra en el producto sin haberlo escrito uno: bibliotecas de terceros,
herramientas de construcción, robots del CI. Es el punto que más protege este proyecto,
porque un cambio malicioso ahí se traduciría en control del computador de quien lo use.

## T

**Tesseract**
El programa que lee texto dentro de imágenes. **Hay que instalarlo aparte.** Si falta,
Automa avisa con las instrucciones concretas para cada sistema operativo.

**Tracking / Seguimiento** · 🔷 propio de Automa
La memoria que tienen algunas recetas entre una ejecución y la siguiente. Son tres
archivos: el que recuerda qué registros ya se usaron en el caso 07, y los dos que guardan
cómo estaba una página la última vez que se miró (casos 23 y 26).
> ⚠️ **No son archivos temporales.** Borrarlos hace que el caso 07 repita registros y que
> el 23 deje de detectar el cambio que estaba vigilando.

**Transición** · 🔷 propio de Automa
La regla que dice a qué paso saltar al terminar el actual, según si salió bien o mal. Es lo
que permite que una receta tenga caminos alternativos.
> ⚠️ Para que una receta se recupere de un fallo, la transición de error debe apuntar a un
> paso **distinto** del que venía a continuación. Si apunta al mismo, el motor no lo
> distingue de «no hay plan B».

## U

**UTC** · *Coordinated Universal Time*
La hora de referencia mundial, sin ajustes de zona horaria ni horario de verano. Automa
guarda todas sus fechas así, **y también interpreta así los horarios programados**. Para
alguien en la zona horaria de Chile continental, «las 9:00» programadas son las 6:00 de la
mañana local.

## V

**Validador** · 🔷 propio de Automa
El programa que revisa las 27 recetas antes de dar el visto bueno: comprueba que cumplan el
formato, que todas sus acciones existan y que sus saltos apunten a pasos reales.
> No comprueba que los valores de cada paso coincidan con lo que la acción espera. Ese
> error solo aparece al ejecutar.

## W

**Webhook** · «gancho web»
Una dirección a la que otro programa puede llamar para disparar una receta.
> **Está desactivado por defecto.** Solo funciona si el operador define una clave de
> acceso.

---

## Convenciones de nombres en este repositorio

| Patrón | Significado | Ejemplo |
|---|---|---|
| `NN_nombre_descriptivo/` | Carpeta de una receta, numerada por orden de creación | `23_web_change_detector/` |
| `familia.accion` | Nombre de una acción | `browser.extract_content` |
| `snake_case` | Variables y funciones de Python | `assert_paths_allowed` |
| `PascalCase` | Clases de Python | `LazyActionRegistry` |
| `_prefijo` | Función interna, no pensada para usarse desde fuera | `_safe_folder` |
| `AUTOMA_*` | Variable de entorno del sistema | `AUTOMA_PANEL_TOKEN` |
| `flujo_*` | Nombre de una métrica publicada | `flujo_runs_total` |
| `AAAAMMDDTHHMMSSffffffZ` | Identificador de una ejecución | `20260827T143052123456Z` |
| `sched_*` | Identificador de un cerrojo tomado por el programador | `sched_20260827T143052…` |

> **Curiosidad histórica:** el prefijo `flujo_` de las métricas es un resto del nombre
> anterior del proyecto. Cambiarlo ahora rompería cualquier panel de vigilancia que ya lo
> esté leyendo, así que se conserva a propósito.

---

**Documentos relacionados:**
[01 · Descripción general](01-system-overview.md) ·
[05 · Referencia técnica](05-technical-reference.md) ·
[17 · Resumen ejecutivo](17-executive-summary.md) ·
[18 · Guía para nuevo desarrollador](18-new-developer-guide.md)
