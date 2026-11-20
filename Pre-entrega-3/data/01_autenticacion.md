# Autenticación en la API de PagoNube

PagoNube es una plataforma ficticia de procesamiento de pagos pensada para
documentar el funcionamiento de una API REST. Todas las solicitudes se hacen
por HTTPS y devuelven JSON.

## URL base

| Ambiente | URL base |
|---|---|
| Producción | `https://api.pagonube.com/v1` |
| Sandbox | `https://sandbox-api.pagonube.com/v1` |

El ambiente sandbox permite probar integraciones sin mover dinero real. Las
API keys de sandbox y de producción son distintas y no son intercambiables.

## API keys

Cada integración se autentica con una API key. Las claves de producción
empiezan con `pn_live_` y las de sandbox con `pn_test_`.

La API key se envía en el header `Authorization` con el esquema `Bearer`:

```http
GET /v1/pagos/pag_123 HTTP/1.1
Host: api.pagonube.com
Authorization: Bearer pn_live_abc123...
```

Nunca se debe incluir la API key en la URL, en el cuerpo de la solicitud ni
en el código fuente. Tampoco debe compartirse por correo o mensajería.

## Vigencia y rotación

Las API keys de PagoNube **expiran a los 90 días corridos** desde su creación.
El sistema envía un aviso por correo 15 días antes del vencimiento.

Para rotar una clave sin cortar el servicio:

1. Crear una clave nueva desde el panel de desarrolladores.
2. Desplegar la clave nueva en la aplicación.
3. Verificar que las solicitudes funcionen.
4. Revocar la clave anterior.

Se pueden tener hasta tres claves activas al mismo tiempo. Esto permite hacer
rotaciones graduales sin interrumpir la integración.

## Permisos o scopes

Cada clave tiene un conjunto de permisos:

| Scope | Permite |
|---|---|
| `payments:read` | Consultar pagos y su estado |
| `payments:write` | Crear pagos |
| `refunds:write` | Crear reembolsos |
| `webhooks:read` | Consultar eventos y entregas de webhooks |

Una clave sin el scope necesario recibe un error `403 forbidden`. El principio
recomendado es otorgar solo los permisos que la integración realmente necesita.

## Firma de webhooks

Además de la API key, cada cuenta tiene un **secreto de webhooks**. PagoNube
firma cada evento con ese secreto en el header `X-PagoNube-Signature`.

La aplicación receptora debe recalcular la firma y compararla usando una
comparación de tiempo constante. Si la firma no coincide, el evento debe
descartarse.

El secreto de webhooks se rota de forma independiente de las API keys. Al
rotarlo, hay que actualizar la aplicación receptora antes de revocar el secreto
anterior.

## Errores de autenticación

| Código HTTP | Código interno | Causa |
|---|---|---|
| `401` | `unauthorized` | Falta el header, la clave es inválida o expiró |
| `403` | `forbidden` | La clave es válida pero no tiene el scope requerido |

Ejemplo de respuesta `401`:

```json
{
  "error": {
    "code": "unauthorized",
    "message": "La API key es inválida o expiró.",
    "request_id": "req_01HZX..."
  }
}
```

El `request_id` identifica la solicitud y debe incluirse al contactar al equipo
de soporte.

## Buenas prácticas

- Guardar las claves en variables de entorno o en un gestor de secretos.
- No commitear archivos `.env` al repositorio.
- Usar claves distintas para sandbox y producción.
- Rotar las claves antes de los 90 días.
- Revisar periódicamente qué claves están activas y revocar las que no se usan.
- Verificar la firma de todos los webhooks antes de procesarlos.

## Preguntas frecuentes

**¿Puedo usar la misma clave en varios servidores?**
Sí, pero se recomienda una clave por aplicación o servicio para poder revocarla
de forma independiente.

**¿Qué pasa si pierdo una clave?**
Hay que revocarla desde el panel y crear una nueva. No es posible recuperar el
valor de una clave existente.

**¿La clave expira si no se usa?**
No. La expiración es por tiempo: 90 días desde la creación, se use o no.

**¿Cómo sé qué clave está usando una solicitud?**
Cada respuesta incluye el `request_id`. El panel de desarrolladores permite
buscar la solicitud y ver la clave asociada, sin mostrar el valor completo.
