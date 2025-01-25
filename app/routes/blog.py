"""Blog routes for the application."""
from flask import Blueprint, render_template, redirect, url_for
import logging

logger = logging.getLogger(__name__)
blog_bp = Blueprint('blog', __name__)


@blog_bp.route('/blog')
def blog():
    """Display list of blog posts."""
    # Sample blog posts - in production, these would come from a database
    posts = [
        {
            'slug': 'how-to-find-quotes-in-youtube-videos',
            'title': 'How to Find Specific Quotes in YouTube Videos',
            'excerpt': (
                'A comprehensive guide to searching through YouTube '
                'content efficiently.'
            ),
            'date': '2024-01-20'
        },
        {
            'slug': 'best-practices-for-content-research',
            'title': 'Best Practices for Content Research Using AudioSnipt',
            'excerpt': (
                'Learn how to use AudioSnipt for content research and '
                'fact-checking.'
            ),
            'date': '2024-01-19'
        }
    ]
    return render_template('blog.html', posts=posts)


@blog_bp.route('/blog/<slug>')
def blog_post(slug):
    """Display individual blog post."""
    # In production, this would fetch from a database
    posts = {
        'how-to-find-quotes-in-youtube-videos': {
            'title': 'How to Find Specific Quotes in YouTube Videos',
            'content': 'Full article content would go here...',
            'date': '2024-01-20'
        },
        'best-practices-for-content-research': {
            'title': 'Best Practices for Content Research Using AudioSnipt',
            'content': 'Full article content would go here...',
            'date': '2024-01-19'
        }
    }
    post = posts.get(slug)
    if post:
        return render_template('blog_post.html', post=post)
    return redirect(url_for('blog.blog'))
