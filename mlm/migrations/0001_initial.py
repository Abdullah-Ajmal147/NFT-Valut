# Generated by Django 5.0.2 on 2025-03-31 00:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("marketplace", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Staking",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("amount", models.DecimalField(decimal_places=8, max_digits=18)),
                ("start_date", models.DateTimeField(auto_now_add=True)),
                ("end_date", models.DateTimeField()),
                (
                    "rewards_claimed",
                    models.DecimalField(decimal_places=8, default=0, max_digits=18),
                ),
                ("is_active", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="StakingPool",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField()),
                ("apy", models.DecimalField(decimal_places=2, max_digits=5)),
                (
                    "min_stake_amount",
                    models.DecimalField(decimal_places=8, max_digits=18),
                ),
                (
                    "max_stake_amount",
                    models.DecimalField(decimal_places=8, max_digits=18),
                ),
                ("lock_period_days", models.IntegerField()),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="Commission",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "commission_type",
                    models.CharField(
                        choices=[
                            ("DIRECT", "Direct Referral"),
                            ("SECOND_LEVEL", "Second Level"),
                            ("STAKING", "Staking Reward"),
                        ],
                        max_length=20,
                    ),
                ),
                ("amount", models.DecimalField(decimal_places=8, max_digits=18)),
                ("is_paid", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                (
                    "transaction",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="commissions",
                        to="marketplace.transaction",
                    ),
                ),
            ],
        ),
    ]
