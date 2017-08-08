from abc import ABCMeta, abstractmethod
from django.utils.timezone import now as tz_now


BACKENDS = []


def register_backend(cls):
    BACKENDS.append('{module}.{qualname}'.format(module=cls.__module__, qualname=cls.__qualname__))


class RegisteredBackend(ABCMeta):
    # provides automatic registration for backend inherited from abstract class with this metaclass
    def __new__(mcls, name, bases, namespace):
        cls = super().__new__(mcls, name, bases, namespace)
        # guards against abstract class
        # expects bases to be empty tuple for abstract class and not empty for concrete classes
        # could be changed to something like this
        if bases != (object,):
            register_backend(cls=cls)
        return cls


class ResidentBackendAbstract(object, metaclass=RegisteredBackend):
    # abstract class that ensures implementation of get_prepared_data method

    @abstractmethod
    def get_prepared_data(self):
        pass


class TestBackend(ResidentBackendAbstract):
    property_external_id = 'test'

    # method that should return data prepared for Resident's creation
    # all backends should have this method
    def get_prepared_data(self):
        common = {'property_external_id': self.property_external_id, 'date': tz_now().date(), 'email': 'test@asdf.com'}
        return [
            dict(common.items(), **{'resident_external_id': 'test_res_1'}),
            dict(common.items(), **{'resident_external_id': 'test_res_2'}),
        ]



