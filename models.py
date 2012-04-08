from django.db import models
from django.contrib.comments.models import Comment as DjangoComment
from django.contrib.comments.managers import CommentManager



class CommentManager(CommentManager):
    def valid(self):
        return self.filter(is_removed = False, is_public = True)


class Comment(DjangoComment):
    """
    This is just a fill-in model.
    """
    class Meta:
        proxy = True

    def __unicode__(self):
        return "%s: %s" % (self.user, self.comment)
