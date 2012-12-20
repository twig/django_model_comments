# This was copied from django.contrib.comments.urls

from django.conf.urls.defaults import *

# This is the only thing changed so it points to model_comments.views.post_comment
urlpatterns = patterns('model_comments.views',
    url(r'^post/$', 'post_comment', name = 'comments-post-comment'),
    url(r'^spam/(?P<comment_id>\d+)$', 'mark_as_spam', name = 'comments-mark-as-spam'),
)

#urlpatterns += patterns('django.contrib.comments.views',
#    url(r'^posted/$',        'comments.comment_done',       name='comments-comment-done'),
#    url(r'^flag/(\d+)/$',    'moderation.flag',             name='comments-flag'),
#    url(r'^flagged/$',       'moderation.flag_done',        name='comments-flag-done'),
#    url(r'^delete/(\d+)/$',  'moderation.delete',           name='comments-delete'),
#    url(r'^deleted/$',       'moderation.delete_done',      name='comments-delete-done'),
#    url(r'^approve/(\d+)/$', 'moderation.approve',          name='comments-approve'),
#    url(r'^approved/$',      'moderation.approve_done',     name='comments-approve-done'),
#)
#
#urlpatterns += patterns('',
#    url(r'^cr/(\d+)/(.+)/$', 'django.views.defaults.shortcut', name='comments-url-redirect'),
#)
