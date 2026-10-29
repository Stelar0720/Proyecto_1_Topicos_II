# Operación de demo local

Esta guía prepara una demostración local, aislada y reiniciable. No usa
Render, una base de producción ni WhatsApp real.

## Credenciales de la demo

| Uso | Valor |
|---|---|
| Panel administrativo | `citafacil-demo-2026` |
| Base de datos | `backend/citafacil-demo.db` |
| Mensajería | Modo demo: no se envían mensajes reales |

El token está sólo en `backend/.env.demo`, archivo ignorado por Git. No lo
reutilicen fuera de esta presentación.

## Arranque antes de las 7

Desde `backend/`, con el entorno virtual activado:

```powershell
.\start_demo.ps1 -Reset
```

El parámetro `-Reset` borra **solamente** `citafacil-demo.db`, vuelve a crear
los servicios, dos citas ejemplo y ocho semanas de datos sintéticos para el
pronóstico. El script se niega a operar sobre otra base de datos.

Mantengan esta consola abierta. En el navegador abran estas URLs HTTP (no los
archivos `file:///` del directorio `frontend/`):

```text
http://127.0.0.1:8000/demo/
http://127.0.0.1:8000/demo/admin.html
http://localhost:8000/docs
```

La ruta `/demo` sirve el frontend desde la misma API local, por lo que detecta
automáticamente el backend correcto. Usen una ventana normal para la página
pública y otra/incógnito para admin si quieren separar las sesiones.

## Recorrido de cuatro minutos

1. **0:00–0:25:** Seleccionar servicio y señalar un domingo cerrado en el
   calendario.
2. **0:25–1:10:** Elegir un horario, reservar con un número chileno ficticio
   y conservar el enlace privado de cancelación.
3. **1:10–1:50:** Abrir el enlace, explicar que sólo previsualiza, confirmar
   la cancelación y volver a mostrar el horario liberado.
4. **1:50–2:35:** Pulsar "Usar mis datos guardados" con el mismo número. Con
   `DEMO_MODE=true`, el OTP aparece prellenado en el cuadro de diálogo. Mostrar
   "Mis próximas citas"; la reserva pública queda vinculada al perfil.
5. **2:35–3:30:** Iniciar sesión en admin con el token de arriba y mostrar
   citas, estadísticas y previsión. Los datos históricos son sintéticos.
6. **3:30–4:00:** Cerrar en `/docs` o mencionar validaciones, cancelación por
   token y las limitaciones de demo.

## Recuperación rápida

Si se toma un horario equivocado, se cierra una pestaña o el historial luce
alterado: detener el servidor (`Ctrl+C`) y repetir `./start_demo.ps1 -Reset`.
No ejecutar `reset_demo.py` con otra variable `DATABASE_URL`.

## Límite de seguridad

El OTP visible es una facilidad exclusiva de la demo y sólo aparece con
`DEMO_MODE=true`. Para cualquier despliegue normal debe permanecer en `false`.
