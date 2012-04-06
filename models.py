from django.db import models
from django.contrib.comments.models import Comment as DjangoComment


class Comment(DjangoComment):
    """
    This is just a fill-in model.
    """
    class Meta:
        proxy = True
