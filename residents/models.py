from importlib import import_module

from django.db import models
from django.utils.timezone import now as tz_now

from residents.backends import BACKENDS


class Property(models.Model):
    # property unique identifier that could be found in third party software
    # max_length=32 only for shorter test data don't know what length actually should be
    external_id = models.CharField(max_length=32, unique=True)

    def __str__(self):
        return 'Property {}'.format(self.external_id)


class ResidentManager(models.Manager):
    # by default show only active residents
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

    def sync(self):
        props = Property.objects.all()
        date = tz_now().date()
        for p in props:
            # prepare sets for property
            property_residents = p.residents.all()
            property_res_logs = ResidentLog.objects.filter(property_external_id=p.external_id, date=date)

            residents_set = set(property_residents.values_list('external_id', flat=True))
            res_logs_set = set(property_res_logs.values_list('resident_external_id', flat=True))

            # delete users that exist in resident set but not exist in log set for this date
            ext_ids_to_delete = residents_set.difference(res_logs_set)
            property_residents.filter(external_id__in=ext_ids_to_delete).update(is_active=False)

            # update users that exist in both sets
            # maybe we should not update all users every time
            # instead add flag to log table and check if user changed from previous date
            ext_ids_to_update = residents_set.intersection(res_logs_set)
            for eid in ext_ids_to_update:
                rl = property_res_logs.get(resident_external_id=eid)
                r = property_residents.get(external_id=eid)
                r.email = rl.email
                r.save()

            # add users from log set that don't exist in resident set
            ext_ids_to_add = res_logs_set.difference(residents_set)
            rlogs_to_add = property_res_logs.filter(resident_external_id__in=ext_ids_to_add)
            to_add = []
            for rl in rlogs_to_add:
                to_add.append(Resident(property=p, external_id=rl.resident_external_id, email=rl.email))
            self.bulk_create(to_add)

        # send mail to newly created users
        for new_res in self.filter(is_email_sent=False):
            new_res.send_mail()


class Resident(models.Model):
    # resident identifier from third party software unique throughout the property
    external_id = models.CharField(max_length=32)
    property = models.ForeignKey(Property, related_name='residents')
    email = models.EmailField()
    # mark residents inactive instead of delete in case something went wrong with sync process
    is_active = models.BooleanField(default=True)
    is_email_sent = models.BooleanField(default=False)

    objects = ResidentManager()
    default_objects = models.Manager()

    class Meta:
        unique_together = ['property', 'external_id']

    def __str__(self):
        return 'Resident {} from property {}({})'.format(self.external_id, self.property.id, self.property.external_id)

    def send_mail(self):
        self.is_email_sent = True
        self.save(update_fields=['is_email_sent'])


class ResidentLogManager(models.Manager):
    # saves data from backends to tmp table

    # code examples
    # https://stackoverflow.com/a/452981/1649855
    # https://stackoverflow.com/a/13808375/1649855
    @staticmethod
    def get_backend_class_from_string(kls_str):
        parts = kls_str.split('.')
        m_name = ".".join(parts[:-1])
        kls_name = parts[-1]
        module = import_module(m_name)
        kls = getattr(module, kls_name)
        return kls

    def collect_data(self):
        for b in BACKENDS:
            try:
                loaded_data = b().get_prepared_data()
            # if string is provided
            except TypeError:
                b_class = self.get_backend_class_from_string(b)
                loaded_data = b_class().get_prepared_data()

            data_for_creation = []
            for ld in loaded_data:
                data_for_creation.append(ResidentLog(**ld))
            self.bulk_create(data_for_creation)


# model to store tmp data got from third-party software
class ResidentLog(models.Model):
    # unique property identifier resident identifier and date
    property_external_id = models.CharField(max_length=32)
    resident_external_id = models.CharField(max_length=32)
    date = models.DateField(db_index=True)
    # field to test update
    email = models.EmailField()

    objects = ResidentLogManager()

    class Meta:
        unique_together = ['property_external_id', 'resident_external_id', 'date']

    def __str__(self):
        return 'Log res_id {}, prop_id {} for {}'.format(self.resident_external_id, self.property_external_id,
                                                         self.date)
