from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Recipe
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


def create_recipe(user, **params):
    defaults = {
        'title': 'Sample Recipe Title',
        'time_minutes': 22,
        'price': Decimal('5.55'),
        'description': 'Sample description',
        'link': 'http://example.com/sample-recipe.pdf'
    }
    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)

RECIPES_URL = reverse('recipe:recipe-list')

class PublicRecipeAPITests(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth required to call API"""
        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateRecipeAPITests(TestCase):
    """Test authenticated API requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@example.com', 'testpass123'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipe_list(self):
        """Test retrieving a list of recipes"""
        create_recipe(user=self.user)
        create_recipe(user=self.user, title='Devilled Eggs')

        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_user(self):
        """Test listing of recipes is limited to authenticated user"""
        other_user = get_user_model().objects.create_user(
            'other_user@example.com', 'testpass123'
        )
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def recipe_url(recipe_id): 
        return reverse('recipe:recipe-detail', args=[recipe_id]) 

    def test_get_recipe_detail(self): 
        """Test getting a recipe detail from the API""" 

        recipe = create_recipe(user=self.user) 
        url = recipe_url(recipe.id) 
        res = self.client.get(url) 

        self.assertEqual(res.status_code, status.HTTP_200_OK) 
        serializer = RecipeDetailSerializer(recipe) 
        self.assertEqual(res.data, serializer.data) 

    def test_create_recipe(self):
        """Test creating a recipe"""
        payload = {
            'title': 'Sample Recipe',
            'time_minutes': '10',
            'price': Decimal('5.55'),
            'description': 'Test recipe description'
        }
        
        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        
        recipe = Recipe.objects.filter(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        
        self.assertEqual(recipe.user, self.user)

    def create_user(self, **params): 
        return get_user_model().objects.create_user(**params)

    def test_partial_update(self):
        """Test PATCH request to Recipe API"""

        original_link = 'https://example.com/sample.pdf'
        recipe = create_recipe(
            user=self.user,
            title='Sample Recipe Title',
            link=original_link
        )

        payload = {'title': 'New Recipe Title'}
        url = recipe_url(recipe.id)
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """Test PUT request of Recipe API"""

        recipe = create_recipe(
            user=self.user,
            title='Sample Recipe Title',
            link='https://example.com/sample.pdf',
            description='Sample Recipe Description'
        )

        payload = {
            'title': 'New Recipe Title',
            'link': 'https://example.com/new-sample.pdf',
            'description': 'New Recipe Description'
        }

        res = self.client.put(recipe_url(recipe.id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()

        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)

        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing recipe user results in error"""

        new_user = create_user(email='user2@example.com', password='test123')
        recipe = create_recipe(user=self.user)
        payload = {'user': new_user.id}

        url = recipe_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test making DELETE request successful"""

        recipe = create_recipe(user=self.user)
        url = recipe_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_users_recipe_error(self):
        """Test deleting another user's recipe raises an error."""
        new_user = create_user(
            email='user2@example.com', password='testpass123'
        )

        recipe = create_recipe(user=new_user)
        url = recipe_url(recipe.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())