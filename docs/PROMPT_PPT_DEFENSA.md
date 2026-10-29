# Prompt para rehacer la presentacion de CitaFacil

Copia el contenido siguiente en GPT para generar una presentacion PPTX editable.

---

Genera una presentacion de 8 diapositivas en espanol para defender individualmente el Proyecto 1 de Topicos Especiales II: CitaFacil. Usa diseno sobrio: azul oscuro, blanco y acento turquesa. Usa poco texto, iconos simples, diagramas claros y notas de presentador de 2 a 4 frases por diapositiva. No inventes decisiones, aprobaciones humanas ni resultados no incluidos a continuacion.

La idea central debe ser: partimos de un sistema full stack existente y lo ampliamos con cinco historias de usuario. No decir que construimos todo desde cero.

## Informacion verificada

### Sistema original

CitaFacil ya era una aplicacion full stack para reservas de pequenos negocios. El sistema original incluia backend FastAPI, SQLAlchemy, SQLite local y PostgreSQL previsto para produccion, frontend HTML CSS JavaScript, Swagger, servicios, reservas, calculo de disponibilidad, prevencion de conflictos, panel administrativo, estadisticas, recordatorios programados e integracion opcional con Twilio WhatsApp.

Twilio ya pertenecia al sistema original. Sin credenciales, registra mensajes en modo demo. El sistema usa CLP, zona horaria America Santiago y telefonos chilenos +56.

### Aporte del equipo

- HU-01 Perfil reutilizable: verificacion por codigo de un solo uso, token temporal y perfil asociado al telefono. El cliente reutiliza sus datos al reservar.
- HU-02 Calendario dinamico: calendario mensual por servicio con dias disponibles, llenos, cerrados y pasados. Reutiliza el motor de disponibilidad de la reserva.
- HU-03 Prevision de demanda: historico y pronostico de siete dias con promedio por dia de semana, advertencias por pocos datos y backtest MAE. Es estadistica explicable, no IA entrenada, y no cambia precios automaticamente.
- HU-04 Cancelacion privada: enlace con token aleatorio; la base guarda solo el hash SHA-256. El GET previsualiza y el POST confirma la cancelacion. Al cancelar, el horario se libera.
- HU-05 Proximas citas: el cliente autenticado consulta unicamente sus citas futuras activas.

### Calidad y GitHub

La version actual tiene 35 pruebas automatizadas aprobadas. La trazabilidad esta en estas ramas y Pull Requests:

| Historia | Rama | PR |
| HU-01 | feature/hu-01-profile-reuse | #1 |
| HU-05 | feature/hu-05-my-appointments | #2 |
| HU-02 | feature/hu-02-calendario-dinamico | #3 |
| HU-04 | feature/hu-04-cancelacion-privada | #4 |
| HU-03 | feature/hu-03-prevision-demanda | #5 |

HU-04 se creo sobre HU-02 y despues se integro a main. Los roles de desarrollo, revision y QA fueron asignados por etapa, pero las aprobaciones humanas formales quedaron pendientes. No atribuir aprobaciones a una persona concreta.

### Decisiones documentadas

- Extender una aplicacion existente en vez de reemplazarla.
- Mantener una prevision simple, reproducible y explicable porque no habia datos suficientes para justificar un modelo entrenado.
- Guardar el hash del token de cancelacion y requerir POST para evitar cancelaciones accidentales.
- Separar el acceso del cliente del acceso administrativo.
- Usar SQLite aislado y Twilio en modo demo para validacion.

Los ajustes recientes de demo, como OTP visible en modo demo, conversion a USD y edicion de precios, no son historias formales. No los presentes como parte de HU-01 a HU-05.

## Estructura obligatoria

### Diapositiva 1 Portada

Titulo: CitaFacil
Subtitulo: Extension de un sistema de reservas mediante historias de usuario
Incluir asignatura, Proyecto 1 e integrantes. Fondo con captura tenue del calendario o reserva.

### Diapositiva 2 Sistema original

Titulo: Punto de partida
Mostrar un diagrama: frontend web, API FastAPI, base de datos y Twilio opcional. Explicar que ya existian reservas, disponibilidad, panel admin, estadisticas, recordatorios y Swagger. Incluir una frase: "El equipo extendio una base funcional, no la reemplazo".

### Diapositiva 3 Objetivo del equipo

Titulo: Necesidades que ampliamos
Mostrar cinco iconos o una secuencia: perfil, calendario, prevision, cancelacion y proximas citas. Explicar que se busco dar mas autonomia al cliente y mejor informacion al administrador.

### Diapositiva 4 HU 01 y HU 05

Titulo: Cliente identificado
Mostrar el flujo telefono, codigo, token, perfil y proximas citas. Explicar que las citas se filtran por el cliente autenticado.

### Diapositiva 5 HU 02 y HU 04

Titulo: Disponibilidad y cancelacion
Columna izquierda: estados available, full, closed y past. Columna derecha: reserva, enlace privado, previsualizacion, confirmacion POST y cupo liberado. Destacar que abrir el enlace no cancela.

### Diapositiva 6 HU 03

Titulo: Prevision de demanda
Mostrar barras de historico y siete dias futuros. Explicar promedio por dia de semana, exclusiones de canceladas, dias cerrados en cero y MAE. Texto visible: "Apoyo para decidir, sin cambiar precios automaticamente".

### Diapositiva 7 Calidad, GitHub y responsabilidades

Titulo: Trazabilidad y validacion
Mostrar la linea de tiempo de PR #1 a #5 y una insignia "35 pruebas automatizadas aprobadas". Incluir esta matriz sin afirmar aprobaciones formales:

| Etapa | Desarrollo | Revision | QA |
| Perfil y proximas citas | Jack | Francisco | Alex |
| Calendario y cancelacion | Francisco | Alex | Jack |
| Prevision | Alex | Jack | Francisco |

Agregar al pie: "Roles asignados por etapa. Confirmaciones humanas formales pendientes".

### Diapositiva 8 Demostracion y cierre

Titulo: Demostracion en cuatro minutos
Secuencia: elegir servicio, reservar, cancelar, consultar proximas citas, abrir admin y mostrar prevision. Cerrar con: "Extendimos una base real con historias trazables, pruebas automatizadas y reglas de negocio verificables".

## Guion de tiempo

- Diapositivas 1 a 3: 2 minutos.
- Diapositivas 4 a 6: 3 minutos.
- Diapositiva 7: 1 minuto.
- Demo: 4 minutos.
- Cierre: 30 segundos.

Entrega solo el PPTX editable. Usa el contenido anterior como fuente unica de afirmaciones.
