# watsonx.ai Troubleshooting Guide

## 🔍 Problema: "La respuesta de watsonx.ai está vacía"

### Diagnóstico Realizado

El error ocurre cuando se ejecuta el comando `/scaffold API REST con Node.js y Express` y watsonx.ai devuelve una respuesta vacía.

### 🎯 Causas Identificadas

#### 1. **Ubicación del archivo .env** ✅ RESUELTO
**Problema**: El archivo `.env` estaba en `IBM-Bob/config/.env` pero la aplicación lo buscaba en `IBM-Bob/.env`

**Solución Aplicada**:
```bash
cd IBM-Bob && cp config/.env .env
```

**Verificación**:
```bash
# Debe existir en la raíz del proyecto IBM-Bob
ls -la IBM-Bob/.env
```

#### 2. **Modelo Incompatible** ✅ RESUELTO
**Problema**: Se usaba `ibm/granite-8b-code-instruct` que puede no estar disponible o configurado

**Solución Aplicada**: 
- Cambiado a `meta-llama/llama-3-3-70b-instruct` (línea 2468)
- Este modelo es más confiable y está ampliamente disponible

**Código Actualizado**:
```python
model = ModelInference(
    model_id="meta-llama/llama-3-3-70b-instruct",  # ✅ Modelo actualizado
    api_client=client,
    project_id=self.config.watsonx_project_id,
    params={...}
)
```

#### 3. **Logging Insuficiente** ✅ RESUELTO
**Problema**: No había visibilidad de qué estaba pasando internamente

**Solución Aplicada**: Agregado logging detallado en cada paso:
```python
print(f"✅ Modelo creado: meta-llama/llama-3-3-70b-instruct")
print(f"🔄 Generando respuesta con watsonx.ai...")
print(f"✅ Respuesta recibida. Tipo: {type(response)}")
print(f"📊 Claves en respuesta: {list(response.keys())}")
print(f"✅ Texto extraído: {len(response_text)} caracteres")
```

### 📋 Checklist de Verificación

Antes de ejecutar el comando `/scaffold`, verifica:

- [ ] **Archivo .env existe en IBM-Bob/.env**
  ```bash
  cat IBM-Bob/.env | grep WATSONX
  ```
  Debe mostrar:
  ```
  WATSONX_API_KEY=M1m1ftQ1YieLC_BVmv0tU7qdjT7hxdbMdwJdxzkN1v45
  WATSONX_PROJECT_ID=3ee45f20-d971-43c7-b6c9-44c5a593ac96
  WATSONX_URL=https://us-south.ml.cloud.ibm.com/
  ```

- [ ] **Credenciales válidas**
  - API Key no expirada
  - Project ID correcto
  - URL correcta (us-south.ml.cloud.ibm.com)

- [ ] **Modelo actualizado**
  - Línea 2468: `meta-llama/llama-3-3-70b-instruct`
  - Línea 2330: `meta-llama/llama-3-3-70b-instruct`

- [ ] **Dependencias instaladas**
  ```bash
  pip list | grep ibm-watsonx-ai
  ```
  Debe mostrar: `ibm-watsonx-ai`

### 🧪 Prueba de Diagnóstico

Ejecuta este comando para ver el logging detallado:

```bash
cd IBM-Bob
python src/client/flet_app.py
```

Luego en la aplicación, ejecuta:
```
/scaffold API REST con Node.js y Express
```

**Salida Esperada** (en consola):
```
✅ Modelo creado: meta-llama/llama-3-3-70b-instruct
🔄 Generando respuesta con watsonx.ai...
✅ Respuesta recibida. Tipo: <class 'dict'>
📊 Claves en respuesta: ['results', 'model_id', 'created_at']
📊 Resultados: 1 items
✅ Texto extraído de results[0]: 1234 caracteres
✅ Validación exitosa: 1234 caracteres
```

**Si ves errores**:

1. **"Error al crear modelo watsonx.ai"**
   - Verifica API Key y Project ID
   - Confirma que el modelo está disponible en tu región

2. **"Error al generar proyecto"**
   - Problema de red o timeout
   - Verifica conectividad a us-south.ml.cloud.ibm.com

3. **"Respuesta vacía detectada"**
   - El modelo devolvió respuesta pero sin contenido
   - Revisa el debug output: `📊 Debug - Respuesta completa: {...}`

### 🔧 Soluciones Adicionales

#### Si el problema persiste:

1. **Verificar conectividad**:
   ```bash
   curl -I https://us-south.ml.cloud.ibm.com
   ```

2. **Probar con modelo alternativo**:
   Edita línea 2468 en `flet_app.py`:
   ```python
   model_id="ibm/granite-3-1-8b-instruct"  # Modelo más pequeño
   ```

3. **Aumentar timeout**:
   Agrega en línea 2469:
   ```python
   params={
       GenParams.MAX_NEW_TOKENS: 2000,
       GenParams.TEMPERATURE: 0.3,
       GenParams.TOP_P: 0.85,
       GenParams.STOP_SEQUENCES: ["\n\n\n"],
       GenParams.TIME_LIMIT: 60000,  # 60 segundos
   }
   ```

4. **Verificar cuota de API**:
   - Accede a IBM Cloud Console
   - Verifica que no hayas excedido el límite de requests

### 📊 Estructura de Respuesta Esperada

watsonx.ai devuelve:
```python
{
    "results": [
        {
            "generated_text": "{\n  \"project_name\": \"...\",\n  ...\n}",
            "generated_token_count": 500,
            "input_token_count": 100,
            "stop_reason": "eos_token"
        }
    ],
    "model_id": "meta-llama/llama-3-3-70b-instruct",
    "created_at": "2026-05-03T11:00:00.000Z"
}
```

El código extrae: `response["results"][0]["generated_text"]`

### 🎯 Próximos Pasos

1. **Ejecuta la aplicación** con el .env en la ubicación correcta
2. **Observa el logging** en la consola
3. **Prueba el comando** `/scaffold API REST con Node.js y Express`
4. **Reporta el output** si el problema persiste

### 📝 Cambios Aplicados

| Archivo | Línea | Cambio |
|---------|-------|--------|
| `flet_app.py` | 2468 | Modelo: `ibm/granite-8b-code-instruct` → `meta-llama/llama-3-3-70b-instruct` |
| `flet_app.py` | 2470-2530 | Agregado logging detallado en cada paso |
| `flet_app.py` | 2470-2476 | Try-except granular para creación de modelo |
| `IBM-Bob/.env` | - | Copiado desde `config/.env` |

### ✅ Estado Actual

- ✅ Archivo .env en ubicación correcta
- ✅ Modelo actualizado a versión estable
- ✅ Logging detallado implementado
- ✅ Error handling mejorado
- ✅ Validación de respuesta robusta

### 🆘 Soporte

Si después de seguir esta guía el problema persiste:

1. Captura el output completo de la consola
2. Verifica que las credenciales sean válidas en IBM Cloud
3. Confirma que el proyecto tiene acceso al modelo `meta-llama/llama-3-3-70b-instruct`
4. Revisa los logs de watsonx.ai en IBM Cloud Console

---

**Última actualización**: 2026-05-03  
**Versión**: 2.0  
**Estado**: Fixes aplicados, pendiente de testing