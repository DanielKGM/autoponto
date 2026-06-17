from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="usuario",
            options={"ordering": ("username",), "verbose_name": "Usuario", "verbose_name_plural": "Usuarios"},
        ),
        migrations.AlterField(
            model_name="usuario",
            name="email",
            field=models.EmailField(blank=True, default="", max_length=254),
        ),
        migrations.AddConstraint(
            model_name="usuario",
            constraint=models.UniqueConstraint(
                fields=("email",),
                condition=~Q(email=""),
                name="uq_usuario_email_preenchido",
            ),
        ),
    ]

