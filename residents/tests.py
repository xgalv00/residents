from django.test import TestCase

from model_mommy import mommy

# Relative imports of the 'app-name' package
from residents.models import Property, Resident, ResidentLog


class ResidentSyncTest(TestCase):
    """
    Class to test resident's sync
    """

    def test_sync(self):
        self.property = mommy.make(Property, external_id='test')
        self.resident_delete = mommy.make(Resident, property=self.property)
        # redefine resident external id from created of dummy method after creation
        self.resident_update = mommy.make(Resident, property=self.property)

        self.assertEqual(ResidentLog.objects.count(), 0)

        # get data from third party software
        ResidentLog.objects.collect_data()

        self.assertEqual(ResidentLog.objects.count(), 2)
        self.assertEqual(ResidentLog.objects.filter(property_external_id=self.property.external_id).count(), 2)

        rl_update = ResidentLog.objects.first()
        rl_add = ResidentLog.objects.last()
        self.resident_update.external_id = rl_update.resident_external_id
        self.resident_update.save()
        self.resident_log_update = ResidentLog.objects.get(resident_external_id=self.resident_update.external_id,
                                                           property_external_id=self.property.external_id)
        self.assertNotEqual(self.resident_update.email, self.resident_log_update.email)
        self.assertFalse(Resident.objects.filter(external_id=rl_add.resident_external_id, property=self.property).exists())

        self.assertTrue(self.resident_delete.is_active)
        self.assertEqual(Property.objects.count(), 1)
        self.assertEqual(Resident.objects.count(), 2)
        # test add resident log does not exist
        self.assertEqual(Resident.objects.filter(property_id=self.property.id).count(), 2)

        Resident.objects.sync()

        self.assertFalse(Resident.default_objects.get(property=self.resident_delete.property, external_id=self.resident_delete.external_id).is_active)
        # redefine default manager to show only active residents
        self.assertEqual(Resident.objects.count(), 2)
        self.assertEqual(Resident.default_objects.count(), 3)
        # test actual update
        self.assertEqual(Resident.objects.get(property=self.resident_update.property, external_id=self.resident_update.external_id).email, self.resident_log_update.email)

        r_added = Resident.objects.get(external_id=rl_add.resident_external_id, property=self.property)
        self.assertTrue(r_added.is_email_sent)




