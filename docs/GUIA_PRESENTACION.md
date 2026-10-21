# Guía de presentación - Proyecto 1: CitaFácil

## Antes de empezar

Esta guía corresponde a la revisión Git
`1e14b3c045e385343fc1809d72b2db9026c86b3d` de `main`. La aplicación original
ya permitía reservar servicios, calcular disponibilidad, administrar citas y
enviar recordatorios por WhatsApp en modo real o demo. El equipo añadió cinco
historias: perfil de cliente, calendario dinámico, previsión de demanda,
cancelación privada y consulta de próximas citas.

**Aclaración importante para la exposición:** la evidencia técnica registra una
revisión y QA asistidos por Codex al integrar el proyecto. Las asignaciones de
roles sí están definidas, pero las firmas o aprobaciones humanas de Reviewer y
QA siguen pendientes. No digan que una persona aprobó una etapa si esa persona
no puede confirmarlo.

Tiempo total sugerido: **12 a 15 minutos**, incluyendo una demostración de 3 a
5 minutos. Cada integrante debe conocer toda la guía, ya que el profesor puede
elegir al presentador al azar.

## Preparación técnica de la demostración

Usen una base de datos local dedicada, no una URL de Render ni una base remota.
En PowerShell, desde `backend/`:

```powershell
$env:DATABASE_URL = "sqlite:///./citafacil-demo.db"
$env:ADMIN_TOKEN = "demo-admin-token"
$env:TWILIO_ACCOUNT_SID = ""
$env:TWILIO_AUTH_TOKEN = ""
$env:TWILIO_WHATSAPP_FROM = ""
python seed.py
python seed_forecast_demo.py
python -m uvicorn app.main:app --reload
```

En otra terminal o navegador, abran `frontend/index.html?api=http://localhost:8000`
y `frontend/admin.html?api=http://localhost:8000`. Para el panel se usa el token
`demo-admin-token`. `seed.py` agrega cinco servicios y dos citas de ejemplo si
la base está vacía. `seed_forecast_demo.py` agrega ocho semanas de **datos
sintéticos**, identificados como tales; sirven para visualizar la previsión y
no se deben presentar como datos reales de un negocio.

Con las credenciales Twilio vacías la aplicación está en modo demo: escribe el
mensaje en el log y no realiza envíos. Esto es útil para la exposición local.
No afirmen que se envió un WhatsApp real si no configuraron Twilio.

Para la historia de perfil, el código OTP se imprime en el log del servidor en
modo demo. Antes de exponer, soliciten el código desde la interfaz y cópienlo
del log para completar el acceso. Si el código no aparece o falla el flujo, no
lo simulen: expliquen el modo demo y muestren la prueba automatizada que cubre
el acceso y las próximas citas.

## Jack García - diapositivas 1 a 3 y tramo de demo de perfil

Duración objetivo: **3:30 a 4:30 minutos**, incluida la demostración breve de
próximas citas.

### Diapositiva 1 - Portada

**Tema:** CitaFácil, Proyecto 1 de Tópicos Especiales II, integrantes y enfoque
de desarrollo asistido por IA.

**Guion sugerido:**

> Buenos días. Somos Jack García, Francisco y Alex Jiménez. Presentamos
> CitaFácil, una aplicación de reservas web que extendimos sobre un proyecto
> existente. Nuestro objetivo no fue medir cuántas líneas produjo una IA, sino
> usarla dentro de un proceso de ingeniería: analizar, implementar, probar,
> revisar y documentar decisiones.

**Mostrar en pantalla:** portada con nombre del curso, integrantes y una captura
del flujo de reservas o del calendario.

**Tiempo:** 30 segundos.

### Diapositiva 2 - Punto de partida y objetivo

**Tema:** qué ofrecía la aplicación base y qué se amplió.

**Guion sugerido:**

> Partimos de una aplicación que ya permitía elegir un servicio, fecha y hora,
> crear una reserva, consultar disponibilidad, administrar servicios y citas, y
> enviar recordatorios por WhatsApp. El backend es FastAPI y el frontend es HTML,
> CSS y JavaScript. Sobre esa base añadimos cinco historias: datos de cliente
> reutilizables, calendario dinámico, previsión, cancelación privada y próximas
> citas. Conservamos las reglas originales de disponibilidad en vez de crear
> motores separados.

**Mostrar en pantalla:** una tabla “base” frente a “agregado por el equipo”.
No decir que se agregó una pasarela de pago: la aplicación base no tenía una.
La HU-01 reutiliza los datos que el formulario de reserva realmente solicita.

**Tiempo:** 1 minuto.

### Diapositiva 3 - Arquitectura

**Tema:** cliente, frontend, API, datos y notificaciones.

**Guion sugerido:**

> El frontend público y el panel administrativo consumen una API REST. FastAPI
> valida solicitudes con Pydantic; SQLAlchemy comunica con SQLite en local y
> puede usar PostgreSQL en producción. La disponibilidad se calcula en el
> servidor para prevenir doble reserva. El panel usa un token de administrador;
> el cliente usa un reto temporal y token de acceso. Twilio es opcional: sin
> credenciales, el sistema registra el mensaje en modo demo y no contacta un
> servicio externo.

**Mostrar en pantalla:** diagrama `Navegador -> FastAPI -> SQLAlchemy ->
SQLite/PostgreSQL`, con flechas opcionales hacia Twilio y el programador de
recordatorios. Añadir `/docs` como evidencia de la API documentada.

**Tiempo:** 1 minuto.

### Demostración de Jack - acceso del cliente y próximas citas

**Acciones:**

1. En la página pública, pulsar **“Usar mis datos guardados”** o **“Ver mis
   próximas citas”**.
2. Ingresar el teléfono de la reserva creada por Francisco.
3. Recuperar el código de seis dígitos desde el log local de modo demo e
   ingresarlo. Si se solicita, guardar el nombre.
4. Pulsar **“Ver mis próximas citas”** y enseñar el servicio, fecha/hora y
   estado de la cita autenticada.

**Resultado esperado:** sólo aparecen citas futuras `pending` o `confirmed` del
cliente autenticado. Sin token el endpoint no entrega las citas.

**Alternativa honesta si falla:** explicar que el OTP local depende del log de
la aplicación y mostrar `tests/test_booking.py`, especialmente
`test_customer_profile_booking_and_private_upcoming` y
`test_customer_invalid_code_cannot_access_data`, junto al resultado actual de
la suite. Eso demuestra el comportamiento probado, no una ejecución manual
que no ocurrió.

**Tiempo:** 1 a 1:30 minutos.

**Transición a Francisco:**

> Con la base y la arquitectura claras, Francisco mostrará las historias de
> reserva y calendario, incluyendo cómo el sistema evita tomar un horario que
> ya fue ocupado.

### Preguntas probables para Jack

| Pregunta | Respuesta breve |
|---|---|
| ¿Cómo evitan el doble booking? | El servidor vuelve a consultar `is_slot_free()` justo antes de crear la cita. Si otro cliente tomó el slot, devuelve HTTP 409. |
| ¿Qué autentica al administrador? | La cabecera `X-Admin-Token`, validada por las rutas `/api/admin`. |
| ¿Qué autentica al cliente? | Un código de acceso de un solo uso y un token temporal Bearer; las próximas citas se filtran por el identificador del cliente autenticado. |
| ¿Se enviaron WhatsApps reales? | En las pruebas y la demo local no; Twilio queda vacío y opera en modo demo. |

## Francisco - diapositivas 4 y 5 y demostración principal

Duración objetivo: **4 a 5 minutos**, incluida la demostración de reserva,
calendario y cancelación.

### Diapositiva 4 - Historias obligatorias

**Tema:** HU-01, HU-02 y HU-03.

**Guion sugerido:**

> Las historias obligatorias cubren tres necesidades. HU-01 permite a un cliente
> recurrente reservar con datos guardados: crea o recupera un perfil autenticado
> y ya no le pide volver a escribir nombre y teléfono. HU-02 muestra un
> calendario mensual con días disponibles, llenos, cerrados y pasados según el
> servicio seleccionado. HU-03 entrega al administrador una previsión para
> apoyar decisiones, sin automatizar precios ni inventario.

**Mostrar en pantalla:** tres tarjetas con el formato “Como..., quiero..., para...”,
una captura del calendario y una del panel de previsión.

**Tiempo:** 1 minuto.

### Diapositiva 5 - Historias adicionales

**Tema:** HU-04 y HU-05.

**Guion sugerido:**

> Elegimos dos historias adicionales. HU-04 permite cancelar con un enlace
> privado. La base de datos guarda sólo el hash del token; abrir el enlace no
> modifica la cita y la cancelación exige un POST de confirmación. Al cancelar,
> el motor de disponibilidad vuelve a ofrecer el horario. HU-05 permite al
> cliente autenticado consultar únicamente sus citas futuras activas.

**Mostrar en pantalla:** flujo `reserva -> cancel_url -> previsualización ->
confirmación POST -> horario liberado` y una nota de que el token no se almacena
en texto plano.

**Tiempo:** 1 minuto.

### Demostración de Francisco - reserva, calendario y cancelación

**Acciones:**

1. En `index.html?api=http://localhost:8000`, seleccionar un servicio.
2. Mostrar en el calendario un día disponible; señalar que los domingos son
   cerrados por defecto y que los días pasados no son seleccionables.
3. Seleccionar una fecha y horario, completar nombre y teléfono chileno válido,
   y reservar.
4. Conservar el enlace privado que aparece en la confirmación. Abrirlo: debe
   mostrar una previsualización sin cancelar aún.
5. Confirmar la cancelación. Volver al calendario o a los horarios y comprobar
   que el mismo horario vuelve a estar disponible.

**Resultado esperado:** reserva `201`, enlace con token, previsualización sin
efecto y una cancelación explícita que deja la cita en `cancelled` y libera el
slot. Si se intenta reservar el mismo slot antes de cancelarlo, la API responde
409.

**Alternativas honestas si falla la interfaz:** abrir `/docs` y ejecutar el
endpoint público de disponibilidad o explicar los casos cubiertos por
`test_calendar_count_updates_after_booking_and_conflict_is_visible` y
`test_explicit_cancel_frees_slot_and_second_attempt_is_rejected`. No presentar
una captura o una prueba como si fuera la ejecución manual del momento.

**Tiempo:** 2 a 3 minutos.

**Transición a Alex:**

> Ya vimos el flujo que usa el cliente. Alex cerrará mostrando cómo verificamos
> calidad y seguridad, qué corrigió el equipo durante el trabajo asistido por IA
> y cómo se construye la previsión del panel administrativo.

### Preguntas probables para Francisco

| Pregunta | Respuesta breve |
|---|---|
| ¿Abrir el enlace cancela la cita? | No. El GET sólo previsualiza; la modificación requiere POST con el token. |
| ¿Por qué no guardar el token plano? | Se guarda SHA-256; si se expone la base, no se revela directamente el enlace privado. |
| ¿Qué pasa con una cita ya pasada o realizada? | La cancelación responde 409 y mantiene el estado. |
| ¿El calendario inventa cupos? | No; usa el mismo motor de disponibilidad que la reserva. |

## Alex Jiménez - diapositivas 6 a 8 y tramo final de demo

Duración objetivo: **3:30 a 4:30 minutos**, incluida la previsión y la evidencia
de pruebas.

### Diapositiva 6 - Calidad y seguridad

**Tema:** cobertura automatizada, seguridad y limitaciones.

**Guion sugerido:**

> Integramos 34 pruebas automatizadas: ocho de la base y perfil, cinco del
> calendario, seis de cancelación y quince de previsión. Cubren teléfonos,
> autenticación administrativa, acceso privado, conflictos de horario, estados
> de calendario, tokens de cancelación, liberación de slots y reglas de la
> previsión. Durante las pruebas, Twilio se fuerza vacío y la base es temporal,
> por lo que no se envían WhatsApps reales ni se usa producción.

**Mostrar en pantalla:** comando `python -m pytest -q` y resultado `34 passed`.
Mencionar que la verificación actual se realizó con dependencias alternativas
compatibles en Python 3.13; la reproducción exacta de los pins requiere Python
3.12.

**Tiempo:** 1 minuto.

### Diapositiva 7 - Intervenciones de IA y correcciones

**Tema:** IA como apoyo, no como autoridad.

**Guion sugerido:**

> Registramos las intervenciones que afectaron el resultado. En HU-02, una
> expectativa inicial de la prueba decía que un servicio de 60 minutos tenía
> diez cupos; al revisar el motor se comprobó que tenía diecinueve inicios
> válidos y se corrigió la prueba, no el motor. En HU-03 se corrigieron la ruta
> temporal de Windows y los datos sembrados del backtest. En HU-04 se corrigió
> un detalle visual de CSS. No hay evidencia registrada de un cambio rechazado
> por una persona específica, así que no lo atribuimos a nadie. La decisión de
> no usar un modelo entrenado para la previsión fue explícita: usamos un método
> estadístico explicable.

**Mostrar en pantalla:** tres ejemplos de `AI_INTERVENTIONS.md`: expectativa
10 vs. 19, portabilidad `/tmp`, y ajuste de datos de backtest. Añadir una caja
“pendiente: aprobaciones humanas por etapa”.

**Tiempo:** 1 minuto.

### Diapositiva 8 - Demostración, roles y cierre

**Tema:** previsión, roles rotados, hallazgos y próximos pasos.

**Guion sugerido:**

> Los roles fueron asignados en rotación: etapa 1, Jack desarrollador,
> Francisco reviewer y Alex QA; etapa 2, Francisco desarrollador, Alex reviewer
> y Jack QA; etapa 3, Alex desarrollador, Jack reviewer y Francisco QA. La
> revisión y QA técnica de integración están documentadas como asistidas por
> Codex; las confirmaciones humanas siguen pendientes. Como próximos pasos,
> debemos formalizar esas firmas, usar Python 3.12 o actualizar dependencias en
> CI, probar PostgreSQL y reemplazar el token de cancelación en URL por un flujo
> más robusto para producción.

**Mostrar en pantalla:** tabla de roles con columna “asignado” y “confirmación
humana pendiente”; lista corta de limitaciones.

**Tiempo:** 45 segundos.

### Demostración de Alex - previsión y pruebas

**Acciones:**

1. Abrir `admin.html?api=http://localhost:8000`, ingresar `demo-admin-token`.
2. Mostrar la tarjeta de previsión creada con datos sintéticos. Señalar ventana
   histórica de 28 días y pronóstico de siete días.
3. Explicar que cuenta citas `pending`, `confirmed` y `done`, excluye
   `cancelled`, usa la media del mismo día de semana y deja la previsión vacía
   si no hay datos.
4. Mostrar el backtest. MAE significa **error absoluto medio**: el promedio de
   la diferencia absoluta entre previsión y valores observados en los días
   evaluados; se expresa en citas por día. Un MAE menor indica menor error en
   ese corte, no garantiza desempeño futuro.
5. Mostrar el resultado de `python -m pytest -q` ya ejecutado o ejecutar la
   suite si el tiempo lo permite.

**Mensaje clave:** no describir HU-03 como modelo de IA entrenado. No entrena
parámetros ni llama a una API de IA; calcula un promedio histórico por día de
la semana. Sus límites incluyen no capturar feriados, promociones, tendencias o
estacionalidad.

**Alternativa honesta si falla el gráfico:** explicar que sin historial el
endpoint advierte `no_data` y deja el pronóstico en `null`. Para una demo visual
se usan sólo los datos sintéticos de `seed_forecast_demo.py`, claramente
identificados. No afirmar que representan ventas reales.

**Tiempo:** 1:30 a 2 minutos.

### Preguntas probables para Alex

| Pregunta | Respuesta breve |
|---|---|
| ¿Es IA la previsión? | No es un modelo de IA entrenado. Es una regla estadística explicable: promedio por día de semana. |
| ¿Qué es MAE? | El promedio de los errores absolutos entre el pronóstico y lo observado, medido en citas por día. |
| ¿Por qué excluir canceladas? | No representan demanda efectiva para planificar capacidad. |
| ¿Qué pruebas se ejecutaron? | La revisión actual ejecutó 34 pruebas y terminó con código 0 en un entorno SQLite aislado. |

## Resumen completo para estudiar

- **Arquitectura:** frontend estático, API FastAPI, validación Pydantic,
  persistencia SQLAlchemy; SQLite local y PostgreSQL previsto para producción.
- **Reserva y doble booking:** el cliente elige servicio, fecha y hora. El
  servidor calcula slots y vuelve a validar antes de crear la cita; el conflicto
  devuelve 409.
- **HU-01 y HU-05:** perfil y token temporal de cliente; la reserva autenticada
  toma nombre/teléfono del perfil; sólo se devuelven próximas citas activas del
  mismo cliente.
- **HU-02:** calendario mensual basado en el motor real; estados `available`,
  `full`, `closed` y `past`.
- **HU-04:** token aleatorio de 32 bytes, hash SHA-256 almacenado, comparación
  de tiempo constante, GET de previsualización y POST de cancelación.
- **HU-03:** 28 días históricos por defecto, siete días futuros, media por día
  de semana, canceladas excluidas, días cerrados en cero, advertencias con pocos
  datos y MAE mediante backtest cuando hay datos suficientes.
- **Calidad:** 34 pruebas actuales verificadas en SQLite; no hay prueba
  documentada contra PostgreSQL ni envío real de WhatsApp durante QA.
- **IA:** generó apoyo de implementación y pruebas, pero se registraron y
  corrigieron resultados equivocados o incompletos. No hay evidencia de que una
  persona concreta haya rechazado un cambio específico.

## Preguntas generales y respuestas

| Tema | Pregunta | Respuesta breve |
|---|---|---|
| Arquitectura | ¿Por qué separar frontend y API? | Facilita que el cliente web y el panel consuman la misma lógica validada en el servidor. |
| Autenticación | ¿El token del cliente es permanente? | No; tiene duración configurada de 30 minutos. |
| Cancelación | ¿Qué ocurre si se reutiliza un enlace? | Tras cancelar, el segundo intento recibe 409; un token de otra cita recibe 404. |
| Doble reserva | ¿Qué pasa si dos personas reservan a la vez? | La segunda validación del servidor rechaza el horario ocupado con 409. |
| Previsión | ¿Por qué no cambia precios sola? | Es apoyo informativo; el administrador conserva la decisión y el método es limitado. |
| Pruebas | ¿Los tests tocaron producción? | No. `conftest.py` fuerza SQLite temporal y Twilio vacío. |
| IA | ¿Qué decisión humana está comprobada? | Están documentadas correcciones técnicas; las aprobaciones humanas formales siguen pendientes. |

## Preparación ante una solicitud de cambio durante la presentación

1. Anotar exactamente el cambio solicitado y clasificarlo: interfaz, endpoint,
   regla de negocio, prueba o configuración.
2. Explicar qué capa se modificaría y qué prueba se añadiría o actualizaría.
3. No implementar directamente en producción ni prometer un resultado no
   verificado. Crear una rama, revisar el impacto y ejecutar la suite.
4. Ejemplos: un nuevo día cerrado afecta configuración y calendario; un cambio
   de cancelación afecta reglas, endpoint y sus seis casos de prueba; cambiar
   la previsión exige explicar método, datos y backtest.

## Pendientes reales de evidencia o confirmación

- Confirmación humana de Reviewer y QA en las tres etapas.
- Reproducción exacta de los pins con Python 3.12 en CI o actualización de los
  pins tras pruebas de compatibilidad.
- Prueba integrada contra PostgreSQL; las pruebas verificadas usan SQLite.
- Configuración real de proveedor OTP/WhatsApp, rate limiting y auditoría.
- Diseño de producción que evite tokens de cancelación en query strings.
- README desactualizado: aún indica 19 pruebas, mientras el código y la
  verificación actual indican 34 tras integrar HU-03 y HU-04.
