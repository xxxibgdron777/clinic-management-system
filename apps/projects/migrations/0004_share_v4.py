from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('projects', '0003_share_v3'),
    ]

    operations = [
        migrations.RenameField(
            model_name='revenueshareconfig',
            old_name='deduction_rate',
            new_name='nurse_fee_rate',
        ),
        migrations.AlterField(
            model_name='revenueshareconfig',
            name='nurse_fee_rate',
            field=models.DecimalField(
                decimal_places=4, default=0.1, max_digits=5,
                help_text='护士服务费 = 收入 × 此比例（仅在勾选"护士服务费"科目时生效）',
                verbose_name='护士服务费比例',
            ),
        ),
        migrations.RenameField(
            model_name='revenueshareconfighistory',
            old_name='deduction_rate',
            new_name='nurse_fee_rate',
        ),
        migrations.AlterField(
            model_name='revenueshareconfighistory',
            name='nurse_fee_rate',
            field=models.DecimalField(
                decimal_places=4, max_digits=5, verbose_name='护士服务费比例',
            ),
        ),
    ]
