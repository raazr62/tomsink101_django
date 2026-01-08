import os
import sys
import django
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

django.setup()

from apps.users.serializers import SignUpSerializer, VerifyEmailOTPSerializer
from django.test.utils import override_settings
from django.core import mail

with override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
    print('Creating user...')
    data = {'email':'verify_test_local@example.com','password':'TestPass123!','name':'Verify Local'}
    s = SignUpSerializer(data=data)
    print('signup valid', s.is_valid(), s.errors)
    user = s.save()
    print('after signup emails:', [m.subject for m in mail.outbox])

    # Find OTP in outbox
    otp = None
    for m in mail.outbox:
        if 'Verify Your Email' in (m.subject or ''):
            match = re.search(r'Your OTP:\s*(\d{6})', m.body)
            if match:
                otp = match.group(1)
                break
    print('Found OTP:', otp)

    # Now verify
    v = VerifyEmailOTPSerializer(data={'email':user.email,'otp_code':otp})
    print('verify valid?', v.is_valid(), v.errors)
    v.save()

    print('after verify emails (subjects):')
    for i,m in enumerate(mail.outbox,1):
        print(i, m.subject)
        print('Alternatives:', getattr(m,'alternatives', []))

    # cleanup
    try:
        user.delete()
        print('Deleted user')
    except Exception as e:
        print('cleanup error', e)
