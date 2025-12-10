"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app
from service import talisman

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"
HTTPS_ENVIRON = {'wsgi.url_scheme': 'https'}

######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)
        talisman.force_https = False

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...

    # Test the READ function with existing account
    def test_get_account(self):
        """It should read a single file"""
        account = self._create_accounts(1)[0]
        resp = self.client.get(
            f"{BASE_URL}/{account.id}", content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["name"], account.name)

    # Test READ function with non-existent acount
    def test_account_not_found(self):
        """This should test response for an account that is not in database"""
        resp = self.client.get(f"{BASE_URL}/0", content_type="application/json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    # Test LIST function with existing account
    def test_list_accoount(self):
        """It should return a list of all accounts in database"""
        self._create_accounts(5)
        resp = self.client.get(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 5)

    # Test Update service ACCOUNT_NOT_FOUNT
    def test_update_account_not_found(self):
        """It should return HTTP 404 ACCOUNT NOT FOUND"""
        # Create an account
        account = self._create_accounts(1)[0]
        # update the account
        account.name = "New Name"  # update the name on the account
        # Send PUT request to server with updated data as a dictionary
        resp = self.client.put(f"{BASE_URL}/2", json=account.serialize())
        # Verify the HTTP status code
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        # # Verify that "name" data was updated
        # updated_account = resp.get_json()
        # self.assertEqual(updated_account["name"], "New Name") # Compare 'name' key values

    # Test update service as per INSTRUCTION
    def test_update_account(self):
        """It should update an account"""
        # Create an account
        test_account = AccountFactory()  # Create account with imported AccountFactory() function
        resp = self.client.post(BASE_URL, json=test_account.serialize())  # POST the account info to server as dict
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)  # Verify status code for creating new account
        # update the test_account
        new_account = resp.get_json()  # Creates a dictionary from the json response object
        new_account["name"] = "New Name"
        resp = self.client.put(f"{BASE_URL}/{new_account['id']}", json=new_account)  # Returns a respose object
        # Verify update success
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        updated_account = resp.get_json()
        self.assertEqual(updated_account["name"], "New Name")

    # Test delete account alternative
    # def test_delete_account(self):
    #   """It should delete an account based on an account ID"""
    #   # Create an account
    #   account = AccountFactory()
    #   resp = self.client.post(BASE_URL, json=account.serialize()) # Send account into database as a dict
    #   self.assertEqual(resp.status_code, status.HTTP_201_CREATED) # Check if resp obj status code correct
    #   # Delete account
    #   new_account = resp.get_json() # Extract data as dictionary from response object int new_account variable
    #   resp = self.client.delete(f"{BASE_URL}/{new_account["id"]}")
    #   self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT) # Check if account is deleted

    # Test delete account
    def test_delete_account(self):
        """It should delete an account based on an account ID"""
        account = self._create_accounts(1)[0]
        resp = self.client.delete(f"{BASE_URL}/{account.id}")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    # Test wrong method request
    def test_method_request_not_allowed(self):
        """It should test for error message when wrong method is requested"""
        resp = self.client.delete(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # Test for security headers
    def test_security_headers(self):
        """This should return security headers"""
        resp = self.client.get('/', environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        headers = {
            'X-Frame-Options': 'SAMEORIGIN',
            'X-Content-Type-Options': 'nosniff',
            'Content-Security-Policy': 'default-src \'self\'; object-src \'none\'',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        for key, value in headers.items():
            self.assertEqual(resp.headers.get(key), value)