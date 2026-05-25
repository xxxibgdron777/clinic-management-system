from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('projects', '0002_share_v2'),
    ]

    operations = [
        migrations.RenameField(
            model_name='revenueshareconfig',
            old_name='partner',
            new_name='project',
        ),
        migrations.AlterField(
            model_name='revenueshareconfig',
            name='project',
            field=models.OneToOneField(
                on_delete=models.CASCADE,
                related_name='share_config',
                to='projects.Project',
                verbose_name='项目',
            ),
        ),
        migrations.RenameField(
            model_name='revenueshareconfighistory',
            old_name='partner',
            new_name='project',
        ),
        migrations.AlterField(
            model_name='revenueshareconfighistory',
            name='project',
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                related_name='share_history',
                to='projects.Project',
                verbose_name='项目',
            ),
        ),
    ]
