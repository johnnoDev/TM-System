# TM System · PetGroom

Sistema de gestión para una tienda/peluquería de mascotas (clientes, mascotas, productos, proveedores, usuarios, horarios, compras, ventas y reportes), desarrollado en Django y SQL Server.

## Requisitos previos

En el equipo donde se va a instalar debe haber:

- **Python 3.12 o superior** (desarrollado y probado con 3.14.4).
- **SQL Server** (Express o superior) con **SQL Server Management Studio** o **Azure Data Studio** para restaurar el backup.
- **ODBC Driver 18 for SQL Server** instalado en el sistema operativo (no es un paquete de Python, es un componente de Windows/driver de conexión). Se instala desde la página oficial de descargas de Microsoft, buscando "ODBC Driver 18 for SQL Server download".
- Git (opcional, solo si vas a clonar el repositorio en vez de copiar la carpeta).

## 1. Restaurar la base de datos (.bak)

1. Copia el archivo `.bak` que se te entregó a una carpeta accesible por el servicio de SQL Server (por ejemplo `C:\Backups\BD_TiendaMascotas.bak`).
2. Abre SQL Server Management Studio y conéctate a tu instancia local.
3. Click derecho en **Databases → Restore Database…**
4. En **Source**, elige **Device** y selecciona el archivo `.bak`.
5. En **Destination**, el nombre de la base debe quedar como `BD_TiendaMascotas` (o el nombre que prefieras, pero después debe coincidir con `DB_NAME` en el paso 4).
6. Antes de confirmar, revisa la pestaña **Files**: si las rutas de los archivos `.mdf`/`.ldf` no existen en el nuevo equipo, marca **Relocate all files to folder** y apunta a una carpeta de datos válida de tu instancia.
7. Click en **OK** para restaurar.

Alternativa por T-SQL (ajusta las rutas según tu instalación):

```sql
RESTORE FILELISTONLY FROM DISK = 'C:\Backups\BD_TiendaMascotas.bak';
-- usa los nombres lógicos que te devuelva el comando anterior en el MOVE

RESTORE DATABASE BD_TiendaMascotas
FROM DISK = 'C:\Backups\BD_TiendaMascotas.bak'
WITH MOVE 'BD_TiendaMascotas' TO 'C:\Program Files\Microsoft SQL Server\MSSQL16.MSSQLSERVER\MSSQL\DATA\BD_TiendaMascotas.mdf',
     MOVE 'BD_TiendaMascotas_log' TO 'C:\Program Files\Microsoft SQL Server\MSSQL16.MSSQLSERVER\MSSQL\DATA\BD_TiendaMascotas_log.ldf',
     REPLACE;
```

## 2. Verificar el acceso a SQL Server

La app se conecta por autenticación de SQL Server (usuario y contraseña, no autenticación de Windows). Asegúrate de que:

- La instancia tenga habilitado **SQL Server and Windows Authentication mode** (Server properties → Security).
- El protocolo **TCP/IP** esté habilitado en SQL Server Configuration Manager, y el servicio se haya reiniciado después de habilitarlo.
- Tengas un login válido con permisos sobre `BD_TiendaMascotas` (puede ser `sa`, o un login dedicado con rol `db_owner` sobre esa base — más recomendable que usar `sa`).

## 3. Crear el entorno virtual e instalar dependencias

Desde la carpeta del proyecto:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Esto instala Django, `mssql-django`, `pyodbc` y `python-dotenv`, entre otros.

## 4. Configurar la conexión a la base de datos

Crea un archivo `.env` en la raíz del proyecto (mismo nivel que `manage.py`) con estas variables:

```
DB_NAME=BD_TiendaMascotas
DB_USER=<tu_usuario_sql>
DB_PASSWORD=<tu_contraseña>
DB_HOST=localhost
DB_PORT=1433
```

Ajusta `DB_HOST`/`DB_PORT` si SQL Server corre en otro equipo o con una instancia nombrada (ej. `localhost\SQLEXPRESS`).

> **Importante:** este `.env` es específico de cada instalación y no debería compartirse ni subirse a un repositorio público — ver la nota de seguridad al final de este documento.

## 5. Aplicar migraciones internas de Django

Las tablas del negocio (clientes, productos, ventas, etc.) ya vienen incluidas en el `.bak` restaurado, así que **no se crean con este paso**. Este comando solo crea/verifica las tablas internas que Django necesita para las sesiones de login y el panel de administración (`django_session`, `django_admin_log`, `auth_*`, etc.):

```powershell
python manage.py migrate
```

## 6. Ejecutar la aplicación

```powershell
python manage.py runserver
```

Abre el navegador en `http://127.0.0.1:8000/`. Debe redirigirte a la pantalla de login.

## 7. Iniciar sesión

Usa un usuario existente de la tabla `TM_M_Usuario` (restaurada junto con el `.bak`). Si no tienes credenciales, se pueden crear/actualizar directamente en SQL Server o desde la pantalla de Usuarios una vez que alguien ya haya iniciado sesión.

## Solución de problemas comunes

| Síntoma | Causa probable |
|---|---|
| `Login failed for user` | Usuario/contraseña incorrectos en `.env`, o SQL Server no tiene habilitada la autenticación mixta. |
| `Data source name not found` / error de driver ODBC | No está instalado el "ODBC Driver 18 for SQL Server" en el equipo. |
| `No se puede conectar` / timeout | Puerto 1433 bloqueado por el firewall, o el protocolo TCP/IP deshabilitado en SQL Server Configuration Manager. |
| Las pantallas cargan pero los combos (ciudad, categoría, etc.) están vacíos | El `.bak` restaurado no incluye datos de catálogo; ejecuta `seed_datos.sql` contra la base. |

## Aviso de seguridad

El archivo `.env` (con la contraseña de SQL Server) y `credenciales.md` (con la contraseña del usuario `admin` de la app) están actualmente versionados en este repositorio y publicados en GitHub. Para una entrega real se recomienda:

1. Quitarlos del control de versiones (`git rm --cached .env credenciales.md`) y agregarlos a `.gitignore`.
2. Rotar (cambiar) la contraseña del login de SQL Server y la del usuario `admin`, ya que quedaron expuestas en el historial del repositorio.
