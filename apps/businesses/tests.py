from django.test import TestCase, Client
from django.urls import reverse
from apps.accounts.models import User
from apps.categories.models import Category
from apps.businesses.models import Business
from apps.dynamic.models import PopularBusinessSearch

class VerifyBusinessSearchTests(TestCase):
    def setUp(self):
        # Create a category
        self.category = Category.objects.create(name="Test Category", slug="test-category", is_active=True)
        
        # Create a user/vendor
        self.user = User.objects.create_user(
            email="vendor@example.com",
            phone="1234567890",
            username="vendor",
            password="testpassword"
        )
        
        # Create a business listing
        self.business = Business.objects.create(
            user=self.user,
            company_name="Domino Pizza Delivery",
            slug="domino-pizza-delivery",
            category=self.category,
            location="New York",
            email="domino@example.com",
            phone="0987654321",
            status="verified"
        )
        
        self.client = Client()

    def test_search_creates_popular_business_search(self):
        # Initial search tracking should not exist
        self.assertEqual(PopularBusinessSearch.objects.count(), 0)

        # Call the search API with query matching "Domino"
        response = self.client.get("/api/businesses/", {"search": "Domino"})
        self.assertEqual(response.status_code, 200)

        # Verify PopularBusinessSearch log was created
        self.assertEqual(PopularBusinessSearch.objects.count(), 1)
        search_log = PopularBusinessSearch.objects.first()
        self.assertEqual(search_log.business, self.business)
        self.assertEqual(search_log.search_count, 1)
        self.assertEqual(search_log.status, "pending")

        # Call search again
        self.client.get("/api/businesses/", {"search": "Domino"})
        search_log.refresh_from_db()
        self.assertEqual(search_log.search_count, 2)

    def test_popular_businesses_api_filtering(self):
        # Create search log
        search_log = PopularBusinessSearch.objects.create(
            business=self.business,
            search_count=5,
            status="pending"
        )

        # Pending search should not be returned by popular-businesses endpoint
        response = self.client.get("/api/dynamic/popular-businesses/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

        # Approve search count
        search_log.status = "approved"
        search_log.save()

        # Approved search should be returned by popular-businesses endpoint
        response = self.client.get("/api/dynamic/popular-businesses/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["company_name"], "Domino Pizza Delivery")
