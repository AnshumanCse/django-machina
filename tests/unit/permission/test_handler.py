# -*- coding: utf-8 -*-

# Standard library imports
# Third party imports
from django.db.models import get_model
from guardian.shortcuts import assign_perm
from guardian.shortcuts import remove_perm

# Local application / specific library imports
from machina.core.loading import get_class
from machina.test.factories import create_category_forum
from machina.test.factories import create_forum
from machina.test.factories import create_link_forum
from machina.test.factories import create_topic
from machina.test.factories import GroupFactory
from machina.test.factories import PostFactory
from machina.test.factories import UserFactory
from machina.test.testcases import BaseUnitTestCase

Forum = get_model('forum', 'Forum')
Post = get_model('conversation', 'Post')
Topic = get_model('conversation', 'Topic')

PermissionHandler = get_class('permission.handler', 'PermissionHandler')


class TestPermissionHandler(BaseUnitTestCase):
    def setUp(self):
        self.u1 = UserFactory.create()
        self.g1 = GroupFactory.create()
        self.u1.groups.add(self.g1)

        # Permission handler
        self.perm_handler = PermissionHandler()

        # Set up a top-level category
        self.top_level_cat = create_category_forum()

        # Set up some forums
        self.forum_1 = create_forum(parent=self.top_level_cat)
        self.forum_2 = create_forum(parent=self.top_level_cat)
        self.forum_3 = create_link_forum(parent=self.top_level_cat)

        # Set up a top-level forum link
        self.top_level_link = create_link_forum()

        # Set up some topics
        self.forum_1_topic = create_topic(forum=self.forum_1, poster=self.u1)
        self.forum_3_topic = create_topic(forum=self.forum_3, poster=self.u1)

        # Set up some posts
        self.post_1 = PostFactory.create(topic=self.forum_1_topic, poster=self.u1)
        self.post_2 = PostFactory.create(topic=self.forum_3_topic, poster=self.u1)

        # Assign some permissions
        assign_perm('can_see_forum', self.u1, self.top_level_cat)
        assign_perm('can_see_forum', self.u1, self.forum_1)
        assign_perm('can_read_forum', self.g1, self.forum_3)

    def test_shows_a_forum_if_it_is_visible(self):
        # Setup
        forums = Forum.objects.filter(pk=self.top_level_cat.pk)
        # Run
        filtered_forums = self.perm_handler.forum_list_filter(forums, self.u1)
        # Check
        self.assertQuerysetEqual(filtered_forums, [self.top_level_cat, ])

    def test_hide_a_forum_if_it_is_not_visible(self):
        # Setup
        forums = Forum.objects.filter(pk=self.top_level_cat.pk)
        # Run
        filtered_forums = self.perm_handler.forum_list_filter(forums, self.u1)
        # Check
        self.assertQuerysetEqual(filtered_forums, [self.top_level_cat, ])

    def test_shows_a_forum_if_all_of_its_ancestors_are_visible(self):
        # Setup
        forums = Forum.objects.filter(parent=self.top_level_cat)
        # Run
        filtered_forums = self.perm_handler.forum_list_filter(forums, self.u1)
        # Check
        self.assertQuerysetEqual(filtered_forums, [self.forum_1, self.forum_3])

    def test_hide_a_forum_if_one_of_its_ancestors_is_not_visible(self):
        # Setup
        remove_perm('can_see_forum', self.u1, self.top_level_cat)
        forums = Forum.objects.filter(parent=self.top_level_cat)
        # Run
        filtered_forums = self.perm_handler.forum_list_filter(forums, self.u1)
        # Check
        self.assertQuerysetEqual(filtered_forums, [])

    def test_knows_the_last_topic_visible_inside_a_forum(self):
        # Run & check : no forum hidden
        last_post = self.perm_handler.get_forum_last_post(self.top_level_cat, self.u1)
        self.assertEqual(last_post, self.post_2)

        # Run & check : one forum hidden
        remove_perm('can_read_forum', self.g1, self.forum_3)
        last_post = self.perm_handler.get_forum_last_post(self.top_level_cat, self.u1)
        self.assertEqual(last_post, self.post_1)

        # Run & check : all forums hidden
        remove_perm('can_see_forum', self.u1, self.forum_1)
        last_post = self.perm_handler.get_forum_last_post(self.top_level_cat, self.u1)
        self.assertIsNone(last_post)

    def test_shows_all_forums_to_a_superuser(self):
        # Setup
        u2 = UserFactory.create(is_superuser=True)
        forums = Forum.objects.filter(parent=self.top_level_cat)
        # Run
        filtered_forums = self.perm_handler.forum_list_filter(forums, u2)
        # Check
        self.assertQuerysetEqual(filtered_forums, [self.forum_1, self.forum_2, self.forum_3])