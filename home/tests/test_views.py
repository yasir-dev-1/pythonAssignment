from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token
from home.models import *
from rest_framework import status
import copy


class UserRegistrationTestCases(APITestCase):
    signup_url = reverse('signup-list')
    login_url = reverse('login-list')
    passwordreset_url = reverse('passwordreset-list')

    user_data = {
        "email": "dummy@gmail.com",
        "username": "dummy",
        "password": "Dummy__"
    }

    def test_user_should_not_register_without_data(self):
        res = self.client.post(self.signup_url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_should_not_login_without_data(self):
        res = self.client.post(self.login_url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_should_register_and_login(self):
        # register user
        res = self.client.post(self.signup_url, self.user_data, format='json')
        self.assertEqual(res.data['email'], self.user_data['email'])
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # login user
        res = self.client.post(self.login_url, self.user_data, format='json')
        self.assertIn('token', res.data)
        self.assertIn('user', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # reset password
        res = self.client.post(self.passwordreset_url, {'email': self.user_data['email']}, format='json')
        self.assertIn('email', res.data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)


class AppTestCases(APITestCase):
    plan_url = reverse('plans-list')
    app_url = reverse('apps-list')
    subscription_url = reverse('subscriptions-list')
    plans = [
        {
            "name": "Free",
            "description": "This is Free plan",
            "price": "$0"
        },
        {
            "name": "Standard",
            "description": "This is Standard plan",
            "price": "$10"
        },
        {
            "name": "Pro",
            "description": "This is Pro plan",
            "price": "$25"
        }
    ]
    app = {
        "name": "App One",
        "description": "This is robotic web app testing framework.",
        "type": "Web",
        "framework": "Django",
        "domain_name": "https://appone.com"
    }
    subscription = {
        "plan": 1,
        "active": True
    }


    def setUp(self):
        User = get_user_model()
        self.user_one = User.objects.create_user(username="dummy_one", password="Dummy1__")
        self.user_two = User.objects.create_user(username="dummy_two", password="Dummy2__")
        self.token_one = Token.objects.create(user=self.user_one)
        self.token_two = Token.objects.create(user=self.user_two)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token_one.key)
        Plan.objects.bulk_create([Plan(**p) for p in self.plans])

    def tearDown(self):
        return super().tearDown()

    # Plan API tests
    def test_single_plan_create_without_auth(self):
        self.client.force_authenticate(user=None)
        res = self.client.post(self.plan_url, self.plans[0], format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_single_plan_update_without_auth(self):
        self.client.force_authenticate(user=None)
        res = self.client.put(reverse('plan-detail', kwargs={'pk': 1}), self.plans[0], format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_single_plan_retrieve_without_auth(self):
        self.client.force_authenticate(user=None)
        res = self.client.get(reverse('plan-detail', kwargs={'pk': 1}))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_all_plans_retrieve_without_auth(self):
        self.client.force_authenticate(user=None)
        res = self.client.get(self.plan_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_single_plan_create(self):
        res = self.client.post(self.plan_url, self.plans[0], format='json')
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_single_plan_update(self):
        res = self.client.put(reverse('plan-detail', kwargs={'pk': 1}), self.plans[0], format='json')
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_single_plan_retrieve(self):
        res = self.client.get(reverse('plan-detail', kwargs={'pk': 1}))
        self.assertEqual(res.data['name'], 'Free')
        self.assertEqual(res.data['price'], '$0')
        self.assertEqual(res.data['description'], 'This is Free plan')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_all_plans_retrieve(self):
        res = self.client.get(self.plan_url)
        self.assertEqual(len(res.data), 3)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    # App API tests
    def test_single_app_create_without_auth(self):
        self.client.force_authenticate(user=None)
        res = self.client.post(self.app_url, self.app, format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_single_app_update_without_auth(self):
        self.client.force_authenticate(user=None)
        res = self.client.put(reverse('app-detail', kwargs={'pk': 1}), self.app, format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_single_app_retrieve_without_auth(self):
        self.client.force_authenticate(user=None)
        res = self.client.get(reverse('app-detail', kwargs={'pk': 1}))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_all_apps_retrieve_without_auth(self):
        self.client.force_authenticate(user=None)
        res = self.client.get(self.plan_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_app_crud(self):
        # creating app
        res = self.client.post(self.app_url, self.app, format='json')
        self.assertEqual(res.data['name'], self.app['name'])
        self.assertEqual(res.data['description'], self.app['description'])
        self.assertEqual(res.data['type'], self.app['type'])
        self.assertEqual(res.data['framework'], self.app['framework'])
        self.assertEqual(res.data['domain_name'], self.app['domain_name'])
        self.assertEqual(res.data['subscription'], None)
        self.assertEqual(res.data['user'], self.user_one.id)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # updating app
        self.updated_app = copy.deepcopy(self.app)
        self.updated_app['type'] = 'Mobile'
        self.updated_app['framework'] = 'React Native'
        self.updated_app['description'] = 'This is robotic mobile app testing framework'
        res = self.client.put(reverse('app-detail', kwargs={'pk': 1}), self.updated_app, format='json')
        self.assertEqual(res.data['name'], self.updated_app['name'])
        self.assertEqual(res.data['description'], self.updated_app['description'])
        self.assertEqual(res.data['type'], self.updated_app['type'])
        self.assertEqual(res.data['framework'], self.updated_app['framework'])
        self.assertEqual(res.data['domain_name'], self.updated_app['domain_name'])
        self.assertEqual(res.data['subscription'], None)
        self.assertEqual(res.data['user'], self.user_one.id)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # retrieving app
        res = self.client.get(reverse('app-detail', kwargs={'pk': 1}))
        self.assertEqual(res.data['name'], self.updated_app['name'])
        self.assertEqual(res.data['description'], self.updated_app['description'])
        self.assertEqual(res.data['type'], self.updated_app['type'])
        self.assertEqual(res.data['framework'], self.updated_app['framework'])
        self.assertEqual(res.data['domain_name'], self.updated_app['domain_name'])
        self.assertEqual(res.data['subscription'], None)
        self.assertEqual(res.data['user'], self.user_one.id)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # retrieving all apps
        res = self.client.get(self.app_url)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # retrieving different user app
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token_two.key)
        res = self.client.get(reverse('app-detail', kwargs={'pk': 1}))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        # deleting app
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token_one.key)
        res = self.client.delete(reverse('app-detail', kwargs={'pk': 1}))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    # Subscription API tests
    def test_single_subscription_create_without_auth(self):
        self.client.force_authenticate(user=None)
        res = self.client.post(self.subscription_url, self.subscription, format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_single_subscription_update_without_auth(self):
        self.client.force_authenticate(user=None)
        res = self.client.put(reverse('subscription-detail', kwargs={'pk': 1}), self.subscription, format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_single_subscription_retrieve_without_auth(self):
        self.client.force_authenticate(user=None)
        res = self.client.get(reverse('subscription-detail', kwargs={'pk': 1}))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_all_subscription_retrieve_without_auth(self):
        self.client.force_authenticate(user=None)
        res = self.client.get(self.subscription_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_subscription_crud(self):
        # creating reference app
        res = self.client.post(self.app_url, self.app, format='json')
        self.assertEqual(res.data['name'], self.app['name'])
        self.assertEqual(res.data['description'], self.app['description'])
        self.assertEqual(res.data['type'], self.app['type'])
        self.assertEqual(res.data['framework'], self.app['framework'])
        self.assertEqual(res.data['domain_name'], self.app['domain_name'])
        self.assertEqual(res.data['subscription'], None)
        self.assertEqual(res.data['user'], self.user_one.id)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # creating subscription
        self.subscription['app'] = res.data['id']
        res = self.client.post(self.subscription_url, self.subscription, format='json')
        self.assertEqual(res.data['app'], self.subscription['app'])
        self.assertEqual(res.data['plan'], self.subscription['plan'])
        self.assertEqual(res.data['active'], self.subscription['active'])
        self.assertEqual(res.data['user'], self.user_one.id)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # updating subscription
        self.updated_subscription = copy.deepcopy(self.subscription)
        self.updated_subscription['plan'] = 2
        self.updated_subscription['active'] = False
        res = self.client.put(reverse('subscription-detail', kwargs={'pk': 1}), self.updated_subscription, format='json')
        self.assertEqual(res.data['app'], self.updated_subscription['app'])
        self.assertEqual(res.data['plan'], self.updated_subscription['plan'])
        self.assertEqual(res.data['active'], self.updated_subscription['active'])
        self.assertEqual(res.data['user'], self.user_one.id)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # retrieving subscription
        res = self.client.get(reverse('subscription-detail', kwargs={'pk': 1}))
        self.assertEqual(res.data['app'], self.updated_subscription['app'])
        self.assertEqual(res.data['plan'], self.updated_subscription['plan'])
        self.assertEqual(res.data['active'], self.updated_subscription['active'])
        self.assertEqual(res.data['user'], self.user_one.id)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # retrieving all subscriptions
        res = self.client.get(self.subscription_url)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # retrieving different user subscription
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token_two.key)
        res = self.client.get(reverse('subscription-detail', kwargs={'pk': 1}))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        # deleting subscription
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token_one.key)
        res = self.client.delete(reverse('subscription-detail', kwargs={'pk': 1}))
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)