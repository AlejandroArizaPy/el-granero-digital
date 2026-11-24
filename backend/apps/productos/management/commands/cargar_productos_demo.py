"""Carga y sincroniza los productos de demostracion del catalogo."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from PIL import Image, UnidentifiedImageError

from apps.productos.models import Categoria, Producto, TipoCategoria
from apps.usuarios.models import Roles, Usuario


@dataclass(frozen=True)
class ProductoDemo:
    nombre: str
    detalle: str
    precio: str
    stock: int
    peso: str
    categoria: str
    imagen: str
    nombres_anteriores: tuple[str, ...] = ()


# Los productos cubren las ocho categorias y usan imagenes locales validas.
PRODUCTOS_DEMO = (
    ProductoDemo(
        "Tomate chonto de temporada",
        "Tomate firme y madurado en planta, ideal para ensaladas y guisos.",
        "3200.00", 42, "1.000", "FYV", "tomate-chonto.jpg",
    ),
    ProductoDemo(
        "Maíz amarillo de cosecha",
        "Grano de maíz seco, seleccionado para arepas, sopas y preparaciones tradicionales.",
        "5200.00", 36, "1.000", "PGC", "icono-maiz.png",
        ("Papa criolla seleccionada",),
    ),
    ProductoDemo(
        "Queso campesino artesanal",
        "Queso fresco de elaboración campesina, ideal para desayunos y preparaciones caseras.",
        "14500.00", 30, "0.500", "LYD", "campesino.jpg",
        ("Zanahoria de huerta",),
    ),
    ProductoDemo(
        "Huevos campesinos por cubeta",
        "Huevos frescos de producción campesina, empacados cuidadosamente para su entrega.",
        "18000.00", 26, "1.800", "HYP", "campesino.jpg",
        ("Cebolla larga fresca",),
    ),
    ProductoDemo(
        "Arepas artesanales de maíz",
        "Arepas elaboradas con maíz molido, listas para asar y acompañar las comidas.",
        "8500.00", 40, "0.500", "DYP", "icono-maiz.png",
        ("Banano criollo",),
    ),
    ProductoDemo(
        "Conserva artesanal de tomate",
        "Conserva de tomate preparada en pequeños lotes para acompañar comidas y panes.",
        "9200.00", 18, "0.300", "DYC", "tomate-chonto.jpg",
        ("Fresas de temporada",),
    ),
    ProductoDemo(
        "Aromática campesina de hierbas",
        "Mezcla seca de hierbas aromáticas para preparar bebidas calientes.",
        "6800.00", 20, "0.100", "BYA", "campesino.jpg",
        ("Tomate cherry de huerta",),
    ),
    ProductoDemo(
        "Semillas de maíz para siembra",
        "Semillas seleccionadas de maíz para iniciar una siembra en huerta o parcela.",
        "7500.00", 34, "0.250", "SMS", "icono-maiz.png",
        ("Papa sabanera para cocina",),
    ),
)


class Command(BaseCommand):
    help = "Previsualiza o sincroniza el catalogo demo del campesino indicado."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            default="DuvanGuerraA",
            help="Usuario campesino existente que será dueño de los productos.",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Escribe productos e imágenes; sin esta opción solo muestra el plan.",
        )

    def handle(self, *args, **options):
        username = options["username"]
        farmer = Usuario.objects.filter(username=username).first()
        if farmer is None:
            raise CommandError(
                f"No existe el usuario {username!r}. Registra primero una cuenta campesino."
            )
        if farmer.rol != Roles.CAMPESINO:
            raise CommandError(f"El usuario {username!r} no tiene rol campesino.")

        # Consulta las categorias oficiales; el modo simulacion no crea filas.
        required_categories = set(TipoCategoria.values)
        categories = {
            categoria.nombre: categoria
            for categoria in Categoria.objects.filter(nombre__in=required_categories)
        }
        missing_categories = sorted(required_categories - categories.keys())

        image_root = settings.BASE_DIR.parent / "frontend" / "public" / "img"
        image_sources = {}
        for producto in PRODUCTOS_DEMO:
            source = image_root / producto.imagen
            if not source.is_file():
                raise CommandError(f"No se encontró la imagen local: {source}")
            try:
                with Image.open(source) as image:
                    image.verify()
            except (OSError, UnidentifiedImageError) as error:
                raise CommandError(f"La imagen no es válida: {source}") from error
            image_sources[producto.imagen] = source

        name_to_demo = {
            name: demo
            for demo in PRODUCTOS_DEMO
            for name in (demo.nombre, *demo.nombres_anteriores)
        }
        existing_products = list(
            Producto.objects.filter(usuario=farmer, nombre__in=name_to_demo).order_by("pk")
        )
        existing_by_demo = {}
        for existing in existing_products:
            demo = name_to_demo[existing.nombre]
            if demo.nombre in existing_by_demo:
                raise CommandError(
                    f"Hay más de un producto identificado como {demo.nombre!r} "
                    f"para {username!r}."
                )
            existing_by_demo[demo.nombre] = existing

        pending = [demo for demo in PRODUCTOS_DEMO if demo.nombre not in existing_by_demo]
        for demo in PRODUCTOS_DEMO:
            existing = existing_by_demo.get(demo.nombre)
            status = "se crearia" if existing is None else "se sincronizaria"
            self.stdout.write(f"{status}: {demo.nombre} ({demo.categoria})")

        if not options["apply"]:
            if missing_categories:
                missing_labels = ", ".join(
                    f"{code} ({TipoCategoria(code).label})"
                    for code in missing_categories
                )
                self.stdout.write(f"Categorias oficiales por crear: {missing_labels}")
            else:
                self.stdout.write("Todas las categorias oficiales requeridas ya existen.")

            self.stdout.write(
                f"Simulacion: {len(pending)} productos por crear; "
                f"{len(existing_by_demo)} por sincronizar. Agrega --apply para guardar."
            )
            return

        # Copia cada imagen a MEDIA_ROOT con nombre por contenido y sin sobrescribir archivos.
        image_names = {
            filename: self._store_image(source)
            for filename, source in image_sources.items()
        }

        with transaction.atomic():
            # Crea solo las categorias oficiales que aun no existen.
            for code in missing_categories:
                category, _created = Categoria.objects.get_or_create(nombre=code)
                categories[code] = category

            # Solo se modifican filas del campesino identificadas por sus nombres demo.
            farmer = Usuario.objects.select_for_update().get(pk=farmer.pk)
            for demo in PRODUCTOS_DEMO:
                existing = existing_by_demo.get(demo.nombre)
                if existing is None:
                    Producto.objects.create(
                        usuario=farmer,
                        nombre=demo.nombre,
                        detalle=demo.detalle,
                        precio=demo.precio,
                        stock=demo.stock,
                        peso=demo.peso,
                        categoria=categories[demo.categoria],
                        imagen=image_names[demo.imagen],
                    )
                    continue

                # Mantiene el ID y el stock actual; actualiza la ficha y categoría demo.
                existing.nombre = demo.nombre
                existing.detalle = demo.detalle
                existing.precio = demo.precio
                existing.peso = demo.peso
                existing.categoria = categories[demo.categoria]
                existing.imagen = image_names[demo.imagen]
                existing.save()

        self.stdout.write(self.style.SUCCESS(
            f"Carga terminada. Creados: {len(pending)}; actualizados: {len(existing_by_demo)}."
        ))

    def _store_image(self, source: Path) -> str:
        content = source.read_bytes()
        digest = sha256(content).hexdigest()
        destination = f"productos/demo_catalogo/{digest[:12]}_{source.name}"

        if default_storage.exists(destination):
            with default_storage.open(destination, "rb") as saved_image:
                if sha256(saved_image.read()).hexdigest() != digest:
                    raise CommandError(f"La imagen destino ya existe con otro contenido: {destination}")
            return destination

        with source.open("rb") as source_file:
            saved_name = default_storage.save(destination, File(source_file, name=source.name))
        if saved_name != destination:
            raise CommandError(f"No se pudo guardar la imagen en la ruta esperada: {destination}")
        return saved_name
