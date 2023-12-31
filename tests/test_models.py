"""
Test cases for Customer Model

"""
import os
import logging
import unittest

from service.models import Customer, DataValidationError, db
from service import app
from tests.factories import CustomerFactory


# from tests.factories import CustomerFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  Customer   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestCustomer(unittest.TestCase):
    """Test Cases for Customer Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        db.drop_all()
        Customer.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Customer).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_object(self):
        """It should create a customer object"""
        customer = Customer(
            first_name="Michael",
            last_name="Parker",
            address="1724 Green Acres Road, Rocky Mount, New York, 00000",
            status=True,
        )
        self.assertEqual(str(customer), "<Customer Michael Parker id=[None]>")
        self.assertTrue(customer is not None)
        self.assertEqual(customer.id, None)
        self.assertEqual(customer.first_name, "Michael")
        self.assertEqual(customer.last_name, "Parker")
        self.assertEqual(
            customer.address, "1724 Green Acres Road, Rocky Mount, New York, 00000"
        )
        self.assertEqual(customer.status, True)

    def test_read_a_customer(self):
        """It should Read a Customer"""
        customer = CustomerFactory()
        logging.debug(customer)
        customer.id = None
        customer.create()
        self.assertIsNotNone(customer.id)
        # Fetch it back
        found_customer = Customer.find(customer.id)
        self.assertEqual(found_customer.id, customer.id)
        self.assertEqual(found_customer.first_name, customer.first_name)
        self.assertEqual(found_customer.last_name, customer.last_name)
        self.assertEqual(found_customer.address, customer.address)

    def test_update_a_customer(self):
        """It should Update a Customer"""
        customer = CustomerFactory()
        logging.debug(customer)
        customer.id = None
        customer.create()
        logging.debug(customer)
        self.assertIsNotNone(customer.id)
        # Change the first name and save it
        customer.first_name = "Joshua"
        original_id = customer.id
        customer.update()
        self.assertEqual(customer.id, original_id)
        self.assertEqual(customer.first_name, "Joshua")
        # Change last name and save it
        customer.last_name = "Williams"
        original_id = customer.id
        customer.update()
        self.assertEqual(customer.id, original_id)
        self.assertEqual(customer.last_name, "Williams")

        # Change the address and save it
        customer.address = "1724 Green Acres Road, Rocky Mount, New York, 10000"
        original_id = customer.id
        customer.update()
        self.assertEqual(customer.id, original_id)
        self.assertEqual(
            customer.address, "1724 Green Acres Road, Rocky Mount, New York, 10000"
        )
        # Fetch it back and make sure the id hasn't changed
        # but the data did change
        customers = Customer.all()
        print(len(customers))
        self.assertEqual(len(customers), 1)
        self.assertEqual(customers[0].id, original_id)
        self.assertEqual(customers[0].first_name, "Joshua")

    def test_update_no_id(self):
        """It should not Update a Customer with no id"""
        customer = CustomerFactory()
        logging.debug(customer)
        customer.id = None
        self.assertRaises(DataValidationError, customer.update)

    def test_delete_a_customer(self):
        """It should Delete a Customer"""
        customer = CustomerFactory()
        customer.create()
        self.assertEqual(len(Customer.all()), 1)
        # delete the customer and make sure it isn't in the database
        customer.delete()
        self.assertEqual(len(Customer.all()), 0)

    def test_list_all_customers(self):
        """It should List all Customers in the database"""
        customers = Customer.all()
        self.assertEqual(customers, [])
        # Create 5 Customers
        for _ in range(5):
            customer = CustomerFactory()
            customer.create()
        # See if we get back 5 customers
        customers = Customer.all()
        self.assertEqual(len(customers), 5)

    def test_serialize_a_customer(self):
        """It should serialize a Customer"""
        customer = CustomerFactory()
        data = customer.serialize()
        self.assertNotEqual(data, None)
        self.assertIn("id", data)
        self.assertEqual(data["id"], customer.id)
        self.assertIn("first_name", data)
        self.assertEqual(data["first_name"], customer.first_name)
        self.assertIn("last_name", data)
        self.assertEqual(data["last_name"], customer.last_name)
        self.assertIn("address", data)
        self.assertEqual(data["address"], customer.address)

    def test_deserialize_a_customer(self):
        """It should de-serialize a Customer"""
        data = CustomerFactory().serialize()
        customer = Customer()
        customer.deserialize(data)
        self.assertNotEqual(customer, None)
        self.assertEqual(customer.id, None)
        self.assertEqual(customer.first_name, data["first_name"])
        self.assertEqual(customer.last_name, data["last_name"])
        self.assertEqual(customer.address, data["address"])

    def test_deserialize_missing_data(self):
        """It should not deserialize a Customer with missing data"""
        data = {"id": 1, "first_name": "Vernon"}
        customer = Customer()
        self.assertRaises(DataValidationError, customer.deserialize, data)

    def test_deserialize_bad_data(self):
        """It should not deserialize bad data"""
        data = "this is not a dictionary"
        customer = Customer()
        self.assertRaises(DataValidationError, customer.deserialize, data)
        data = {
            "id": 1,
            "first_name": "abc",
            "last_name": "def",
            "address": "ghi",
            "active": "not Boolean",
        }
        self.assertRaises(DataValidationError, customer.deserialize, data)

    def test_find_customer(self):
        """It should Find a Customer by ID"""
        customers = CustomerFactory.create_batch(5)
        for customer in customers:
            customer.create()
        logging.debug(customers)
        # make sure they got saved
        self.assertEqual(len(Customer.all()), 5)
        # find the 2nd customer in the list
        customer = Customer.find(customers[1].id)
        self.assertIsNot(customer, None)
        self.assertEqual(customer.id, customers[1].id)
        self.assertEqual(customer.first_name, customers[1].first_name)
        self.assertEqual(customer.last_name, customers[1].last_name)
        self.assertEqual(customer.address, customers[1].address)

    def test_find_by_name(self):
        """It should find customers by full name"""
        customers = CustomerFactory.create_batch(10)
        for customer in customers:
            customer.create()
        # Use the first customer's name for the search
        first_name = customers[0].first_name
        last_name = customers[0].last_name
        # Get the count of customers with the same full name
        count = len(
            [
                customer
                for customer in customers
                if customer.first_name == first_name and customer.last_name == last_name
            ]
        )
        # Use the new method to find customers by full name
        found = Customer.find_by_name(first_name, last_name)
        self.assertEqual(found.count(), count)
        for customer in found:
            self.assertEqual(customer.first_name, first_name)
            self.assertEqual(customer.last_name, last_name)

    def test_find_by_first_name(self):
        """It should Find customers by First Name"""
        customers = CustomerFactory.create_batch(10)
        for customer in customers:
            customer.create()
        first_name = customers[0].first_name
        count = len(
            [customer for customer in customers if customer.first_name == first_name]
        )
        found = Customer.find_by_first_name(first_name)
        self.assertEqual(found.count(), count)
        for customer in found:
            self.assertEqual(customer.first_name, first_name)

    def test_find_by_last_name(self):
        """It should Find customers by Last Name"""
        customers = CustomerFactory.create_batch(10)
        for customer in customers:
            customer.create()
        last_name = customers[0].last_name
        count = len(
            [customer for customer in customers if customer.last_name == last_name]
        )
        found = Customer.find_by_last_name(last_name)
        self.assertEqual(found.count(), count)
        for customer in found:
            self.assertEqual(customer.last_name, last_name)

    def test_find_by_address(self):
        """It should Find customers by Last Name"""
        customers = CustomerFactory.create_batch(10)
        for customer in customers:
            customer.create()
        address = customers[0].address
        count = len([customer for customer in customers if customer.address == address])
        found = Customer.find_by_address(address)
        self.assertEqual(found.count(), count)
        for customer in found:
            self.assertEqual(customer.address, address)
