from models import Like

delatable_objects = Like.objects.all()[:]
for m in delatable_objects:
    m.delete()