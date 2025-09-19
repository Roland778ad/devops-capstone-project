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

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"


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
        resp = self.client.get (
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

    # # Test Update service
    # def test_update_account(self):
    #     """It should update an account"""
    #     # Create an account
    #     account = self._create_accounts(1)[0]
    #     # update the account
    #     resp = self.client.get(f"{BASE_URL}/0", content_type="application/json") # recall the account
    #     new_account = resp.get_json()
    #     new_account["name"] = "New Data" # Over write the name in the account
    #     resp2 = self.client.put(f"{BASE_URL}/0", json=new_account) # Send PUT request to server to update the data in database
    #     # Verify that data was updated
    #     updated_account = resp2.get_json() # Get JSON type data from the update's response message
    #     self.assertEqual(updated_account["name"], "New Data") # Compare new data's 'name' element values
    #     # Verify the HTTP status code
    #     self.assertEqual(resp.status_code, status.HTTP_200_OK)

    # Test update service as per INSTRUCTION
    def test_update_account(self):
      """It should update an account"""
      # Create an account
      test_account = AccountFactory() # Create account with imported AccountFactory() function
      resp = self.client.post(BASE_URL, json=test_account.serialize()) # POST the account info to server
      self.assertEqual(resp.status_code, status.HTTP_201_CREATED) # Verify status code for creating new account
      # update the test_account
      new_account = resp.get_json()
      new_account["name"] = "Something Known"
      resp = self.client.put(f"{BASE_URL}/{new_account['id']}", json=new_account)
      # Verify update success
      self.assertEqual(resp.status_code, status.HTTP_200_OK)
      updated_account = resp.get_json()
      self.assertEqual(updated_account["name"], "Something Known")       
    
