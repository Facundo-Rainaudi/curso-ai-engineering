# Creación de pagos

Este documento describe cómo crear un pago con la API de PagoNube y cómo
interpretar su ciclo de vida.

## Endpoint

```http
POST /v1/pagos
```

Headers obligatorios:

| Header | Valor |
|---|---|
| `Authorization` | `Bearer pn_live_...` |
| `Content-Type` | `application/json` |
| `Idempotency-Key` | Un identificador único por operación |

## Cuerpo de la solicitud

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `amount` | entero | Sí | Monto en la unidad mínima de la moneda |
| `currency` | string | Sí | `ARS`, `USD` o `BRL` |
| `customer` | objeto | Sí | Datos mínimos del pagador |
| `payment_method` | objeto | Sí | Medio de pago elegido |
| `description` | string | No | Descripción visible para el cliente |
| `metadata` | objeto | No | Datos libres para uso interno |

El campo `amount` se expresa en la unidad mínima de la moneda. Por ejemplo,
`150000` en ARS representa 1.500,00 ARS. El mínimo permitido por operación es
`100` y el máximo es `5000000` en la unidad mínima.

Las monedas aceptadas son **peso argentino (ARS)**, **dólar estadounidense
(USD)** y **real brasileño (BRL)**. Otras monedas reciben un error
`422 validation_error`.

## Ejemplo de solicitud

```json
{
  "amount": 150000,
  "currency": "ARS",
  "customer": {
    "email": "cliente@ejemplo.com",
    "name": "Ana Pérez"
  },
  "payment_method": {
    "type": "card",
    "token": "tok_01HZX..."
  },
  "description": "Suscripción mensual",
  "metadata": {
    "order_id": "ORD-1042"
  }
}
```

## Idempotencia

El header `Idempotency-Key` evita crear pagos duplicados si la aplicación
reintenta una solicitud por un timeout o un error de red.

Si se envía la misma `Idempotency-Key` dentro de las **24 horas** siguientes,
PagoNube devuelve el mismo pago, sin crear uno nuevo. La clave debe ser un
identificador único, por ejemplo un UUID v4.

Si se reutiliza la misma clave con un cuerpo diferente, la API responde `409
conflict`.

## Respuesta

```json
{
  "id": "pag_01HZX...",
  "status": "pendiente",
  "amount": 150000,
  "currency": "ARS",
  "created_at": "2026-03-10T14:32:00Z",
  "payment_method": {
    "type": "card",
    "brand": "visa",
    "last4": "4242"
  }
}
```

## Estados del pago

| Estado | Significado |
|---|---|
| `pendiente` | El pago fue creado y está siendo procesado |
| `aprobado` | El pago se completó correctamente |
| `rechazado` | El medio de pago rechazó la operación |
| `reembolsado` | El pago fue devuelto total o parcialmente |
| `contracargo` | El cliente inició un contracargo |

El estado puede cambiar de forma asíncrona. Por eso la integración no debe
asumir que un pago queda aprobado en la misma respuesta de creación.

## Webhooks de pagos

PagoNube envía eventos cuando cambia el estado de un pago:

| Evento | Cuándo se envía |
|---|---|
| `payment.approved` | El pago pasa a `aprobado` |
| `payment.rejected` | El pago pasa a `rechazado` |
| `payment.refunded` | Se registra un reembolso |
| `payment.chargeback` | Se registra un contracargo |

La aplicación debe responder con un código `2xx` en menos de 5 segundos. Si no
lo hace, PagoNube reintenta la entrega según la política descripta en el
documento de límites y errores.

## Autenticación fuerte del cliente (3DS)

Para tarjetas, el campo `payment_method.three_ds` permite indicar si se solicita
autenticación fuerte. Si el emisor la requiere, el pago queda en estado
`pendiente` hasta que el cliente complete el desafío.

La URL de redirección se envía en `three_ds.return_url`. PagoNube no almacena
datos sensibles de la tarjeta: solo recibe un token generado por el SDK.

## Errores frecuentes al crear pagos

| Código | Causa probable |
|---|---|
| `400 invalid_request` | JSON mal formado o falta un header |
| `409 conflict` | `Idempotency-Key` reutilizada con otro cuerpo |
| `422 validation_error` | Moneda no soportada o monto fuera de rango |
| `429 rate_limit_exceeded` | Se superó el límite de solicitudes |

## Buenas prácticas

- Generar una `Idempotency-Key` nueva por cada pago distinto.
- Guardar el `id` del pago y el `request_id` para trazabilidad.
- No confiar solo en la respuesta de creación: escuchar los webhooks.
- Validar el monto y la moneda antes de enviar la solicitud.
- Reintentar solo errores transitorios (`429`, `500`, `503`), nunca errores
  de validación (`422`).
