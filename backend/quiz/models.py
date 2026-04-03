import uuid

from django.db import models


class Event(models.Model):
    month = models.PositiveSmallIntegerField(db_index=True)
    day = models.PositiveSmallIntegerField(db_index=True)
    year = models.IntegerField()
    description = models.TextField()
    pages = models.TextField(blank=True, default='')

    class Meta:
        indexes = [
            models.Index(fields=['month', 'day']),
        ]

    def __str__(self):
        return f'{self.year}-{self.month:02d}-{self.day:02d}: {self.description[:60]}'


class Player(models.Model):
    name = models.CharField(max_length=50, unique=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
