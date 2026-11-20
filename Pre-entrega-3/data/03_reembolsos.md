# Reembolsos

La API de PagoNube permite devolver total o parcialmente un pago aprobado.
Un reembolso siempre se asocia a un pago existente y nunca puede superar el
monto original.

## Endpoint

```http
POST /v1/reembolsos
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
| `payment_id` | string | Sí | Identificador del pago original |
| `amount` | entero | Sí | Monto a devolver en la unidad mínima |
| `reason` | string | No | Motivo del reembolso |

El `amount` se expresa en la misma moneda del pago original. Para un reembolso
total, debe ser igual al monto del pago. Para un reembolso parcial, debe ser
menor.

## Plazos

Los plazos se cuentan en días corridos desde la fecha de **aprobación** del pago,
no desde la fecha de creación.

| Tipo de reembolso | Plazo máximo |
|---|---|
| Reembolso total | **30 días corridos** desde la aprobación |
| Reembolso parcial | **15 días corridos** desde la aprobación |

Pasado el plazo, la API responde `422 validation_error` con el código
`refund_window_expired`. En ese caso el reembolso debe gestionarse por fuera de
la API.

## Reembolsos totales

Un reembolso total devuelve el monto completo del pago y pasa el pago al estado
`reembolsado`. Solo se permite un reembolso total por pago.

Ejemplo:

```json
{
  "payment_id": "pag_01HZX...",
  "amount": 150000,
  "reason": "Cancelación de la suscripción"
}
```

## Reembolsos parciales

Se pueden hacer varios reembolsos parciales sobre el mismo pago, siempre que la
suma no supere el monto original. Cada reembolso parcial debe solicitarse dentro
de los **15 días corridos** posteriores a la aprobación.

Ejemplo: si un pago fue de 150000, se pueden devolver 50000 y luego 30000, pero
no 120000 después, porque la suma daría 200000 y superaría el total.

Si la suma de los reembolsos existentes más el nuevo supera el monto original,
la API responde `422 validation_error` con el código
`refund_amount_exceeds_payment`.

## Respuesta

```json
{
  "id": "ref_01HZX...",
  "payment_id": "pag_01HZX...",
  "amount": 150000,
  "currency": "ARS",
  "status": "solicitado",
  "created_at": "2026-03-12T10:15:00Z"
}
```

## Estados del reembolso

| Estado | Significado |
|---|---|
| `solicitado` | El reembolso fue recibido y está en proceso |
| `procesado` | El dinero fue devuelto al cliente |
| `rechazado` | El reembolso no pudo completarse |

El paso de `solicitado` a `procesado` puede demorar entre **5 y 10 días
hábiles**, según el medio de pago y el banco emisor. PagoNube no controla los
tiempos internos de cada banco.

## Comisiones

En un reembolso total, PagoNube devuelve el monto neto que recibió el comercio.
La comisión de la plataforma no se reintegra.

En un reembolso parcial, la comisión original se mantiene sin cambios. No se
recalcula la comisión ni se devuelve una parte proporcional.

## Idempotencia

Igual que en la creación de pagos, el header `Idempotency-Key` evita duplicar
reembolsos. Si se repite la misma clave dentro de las 24 horas, se devuelve el
mismo reembolso. Si se repite la clave con otro cuerpo, la API responde `409
conflict`.

## Webhooks de reembolsos

| Evento | Cuándo se envía |
|---|---|
| `refund.created` | Se creó un reembolso |
| `refund.processed` | El reembolso fue procesado |
| `refund.rejected` | El reembolso fue rechazado |

La aplicación debe verificar la firma del webhook antes de actualizar su estado
interno.

## Errores frecuentes

| Código | Causa |
|---|---|
| `404 not_found` | El `payment_id` no existe |
| `409 conflict` | `Idempotency-Key` reutilizada con otro cuerpo |
| `422 refund_window_expired` | Se superó el plazo permitido |
| `422 refund_amount_exceeds_payment` | La suma de reembolsos supera el pago |
| `422 validation_error` | Monto inválido o moneda incorrecta |

## Buenas prácticas

- Verificar el estado del pago antes de solicitar un reembolso.
- Usar una `Idempotency-Key` distinta por cada reembolso.
- Registrar el `id` del reembolso y el `payment_id` asociado.
- Escuchar los webhooks para conocer el estado final.
- No reintentar errores `422`: son errores de validación y volverán a fallar.
