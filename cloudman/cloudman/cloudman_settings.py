from django.conf import settings

SUPER_USER_GROUPS = getattr(settings, 'SUPER_USER_GROUPS',['cloudman-admins','it-dep-pes-ps',])
