from model_comments.forms import CommentForm



def get_subsubclasses_for(klass):
    subclasses = []
    
    for cls in klass.__subclasses__():
        subclasses.append(cls)
        
        if len(cls.__subclasses__()) > 0:
            subclasses.extend(get_subsubclasses_for(cls))

    return subclasses




def get_form_class_for_object(obj):
    # Find subclasses of CommentForm and see which one we should display
    #print get_subsubclasses_for(CommentForm)
    
    for cls in get_subsubclasses_for(CommentForm):
        # Instantiate class
        f = cls(obj)

        try:
            if f.is_form_for_object(obj):
                return cls
        except NotImplementedError:
            pass

    # If no form, revert to default form
    return CommentForm
