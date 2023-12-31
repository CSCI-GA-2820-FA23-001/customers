"""
TestYourResourceModel API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from urllib.parse import quote_plus
from service import app

from service.models import db, init_db, Customer
from service.common import status  # HTTP Status Codes
from tests.factories import CustomerFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/testdb"
)
BASE_URL = "/api/customers"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestYourResourceServer(TestCase):
    """REST API Server Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Customer).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    ######################################################################
    #  P L A C E   T E S T   C A S E S   H E R E
    ######################################################################
    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["status"], "OK")

    def _create_customers(self, count):
        """Factory method to create customers in bulk"""
        customers = []
        for _ in range(count):
            test_customer = CustomerFactory()
            response = self.client.post(BASE_URL, json=test_customer.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test customer",
            )
            new_customer = response.get_json()
            test_customer.id = new_customer["id"]
            customers.append(test_customer)
        return customers

    def test_index(self):
        """It should call the home page"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_get_customer_list(self):
        """It should Get a list of Customers"""

        self._create_customers(5)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 5)

    def test_get_customer(self):
        """It should Get a single Customer"""
        # create a customer to read
        test_customer = CustomerFactory()
        response = self.client.post(BASE_URL, json=test_customer.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # get the id of a customer
        # print(test_customer.id, response.get_json()["id"])
        test_customer.id = response.get_json()["id"]
        response = self.client.get(f"{BASE_URL}/{test_customer.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["id"], test_customer.id)
        self.assertEqual(data["first_name"], test_customer.first_name)
        self.assertEqual(data["last_name"], test_customer.last_name)
        self.assertEqual(data["address"], test_customer.address)

    def test_get_customer_not_found(self):
        """It should not Get a Customer thats not found"""
        response = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        logging.debug("Response data = %s", data)
        self.assertIn("was not found", data["message"])

    def test_update_customer(self):
        """It should Update an existing Customer"""
        # create a customer to update
        test_customer = CustomerFactory()
        response = self.client.post(BASE_URL, json=test_customer.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # update the customer
        new_customer = response.get_json()
        logging.debug(new_customer)
        new_customer["address"] = "unknown"
        response = self.client.put(
            f"{BASE_URL}/{new_customer['id']}", json=new_customer
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_customer = response.get_json()
        self.assertEqual(updated_customer["address"], "unknown")

    def test_delete_customer(self):
        """It should Delete a Customer"""
        test_customer = CustomerFactory()
        response = self.client.post(BASE_URL, json=test_customer.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        test_customer.id = response.get_json()["id"]
        response = self.client.delete(f"{BASE_URL}/{test_customer.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)
        response = self.client.get(f"{BASE_URL}/{test_customer.id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_restore_customer(self):
        """It should restore a Customer"""
        test_customer = CustomerFactory()
        response = self.client.post(BASE_URL, json=test_customer.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        test_customer.id = response.get_json()["id"]
        response = self.client.put(f"{BASE_URL}/{test_customer.id}/deactivate")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(f"{BASE_URL}/{test_customer.id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.put(f"{BASE_URL}/{test_customer.id}/restore")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(f"{BASE_URL}/{test_customer.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["id"], test_customer.id)
        self.assertEqual(data["active"], True)

    def test_query_customer_list_by_name(self):
        """It should Query Customers by Name"""
        customers = self._create_customers(10)
        test_first_name = customers[0].first_name
        test_last_name = customers[0].last_name
        response = self.client.get(
            BASE_URL,
            query_string=f"first_name={quote_plus(test_first_name)}&last_name={quote_plus(test_last_name)}",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        full_name_customers = [
            customer
            for customer in data
            if customer["first_name"] == test_first_name
            and customer["last_name"] == test_last_name
        ]
        # Check the data just to be sure
        for customer in full_name_customers:
            self.assertEqual(customer["first_name"], test_first_name)
            self.assertEqual(customer["last_name"], test_last_name)

    def test_query_customer_list_by_first_name(self):
        """It should Query Customers by First Name"""
        customers = self._create_customers(10)
        test_first_name = customers[0].first_name
        response = self.client.get(
            BASE_URL, query_string=f"first_name={quote_plus(test_first_name)}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        last_name_customers = [
            customer for customer in data if customer["first_name"] == test_first_name
        ]
        # check the data just to be sure
        for customer in last_name_customers:
            self.assertEqual(customer["first_name"], test_first_name)

    def test_query_customer_list_by_last_name(self):
        """Query Customers by last name"""
        customers = self._create_customers(10)
        test_last_name = customers[0].last_name
        response = self.client.get(
            BASE_URL, query_string=f"last_name={quote_plus(test_last_name)}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        last_name_customers = [
            customer for customer in data if customer["last_name"] == test_last_name
        ]
        # check the data just to be sure
        for customer in last_name_customers:
            self.assertEqual(customer["last_name"], test_last_name)

    def test_query_customer_list_by_address(self):
        """Query Customers by address"""
        customers = self._create_customers(10)
        test_address = customers[0].address
        response = self.client.get(
            BASE_URL, query_string=f"address={quote_plus(test_address)}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        address_customers = [
            customer for customer in data if customer["address"] == test_address
        ]
        # check the data just to be sure
        for customer in address_customers:
            self.assertEqual(customer["address"], test_address)

    ######################################################################
    #  T E S T   S A D   P A T H S
    ######################################################################

    def test_update_no_id(self):
        """Return not found if the customer id does not exist"""
        # Test the status code
        response = self.client.put(f"{BASE_URL}/{'123'}", json={"address": "unknown"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_status(self):
        """It is not allowed updating the status through PUT"""
        test_customer = CustomerFactory()
        response = self.client.post(BASE_URL, json=test_customer.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # update the customer
        new_customer = response.get_json()
        logging.debug(new_customer)
        new_customer["active"] = False
        response = self.client.put(
            f"{BASE_URL}/{new_customer['id']}", json=new_customer
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_customer_no_data(self):
        """It should not Create a customer with missing data"""
        response = self.client.post(BASE_URL, json={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_method_not_allowed(self):
        """It should use method not defined in routes"""
        response = self.client.put(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_unsupported_media_type(self):
        """It should request with unsupported media type"""
        response = self.client.post(
            BASE_URL, data="", headers={"Content-Type": "application/xml"}
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_restore_invalid_id(self):
        """It should return 404 not found"""
        response = self.client.put(f"{BASE_URL}/{'193759541'}/restore")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_deactivate_invalid_id(self):
        """It should return 404 not found"""
        response = self.client.put(f"{BASE_URL}/987654321/deactivate")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
