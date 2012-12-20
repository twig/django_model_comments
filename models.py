from django.db import models
from django.contrib.comments.models import Comment as DjangoComment
from django.contrib.comments.managers import CommentManager
from django.contrib.sites.models import Site



class CommentManager(CommentManager):
    def for_site(self, site = None):
        if site is None:
            site = Site.objects.get_current()

        return self.filter(site = site)

    
    def valid(self):
        return self.for_site().filter(is_removed = False, is_public = True)


class Comment(DjangoComment):
    """
    This is just a fill-in model.
    """
    class Meta:
        proxy = True

    objects = CommentManager()

    def __unicode__(self):
        return "%s: %s" % (self.user, self.comment)
