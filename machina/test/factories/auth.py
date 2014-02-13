# -*- coding: utf-8 -*-

# Standard library imports
# Third party imports
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
import factory

# Local application / specific library imports
from machina.test.factories import random_string


class UserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = User
    username = factory.LazyAttribute(lambda t: random_string(length=15))
    email = factory.Sequence(lambda n: 'test{0}@example.com'.format(n))
    password = '1234'
    is_active = True

    @classmethod
    def _prepare(cls, create, **kwargs):
        password = kwargs.pop('password', None)
        user = super(UserFactory, cls)._prepare(create, **kwargs)
        if password:
            user.set_password(password)
            if create:
                user.save()
        return user


class GroupFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Group
    name = factory.LazyAttribute(lambda t: random_string())