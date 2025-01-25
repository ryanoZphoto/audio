from flask import Blueprint, Response
from datetime import datetime

seo_bp = Blueprint('seo', __name__)


@seo_bp.route('/sitemap.xml')
def sitemap():
    """Generate sitemap.xml"""
    pages = []
    
    # Add static pages
    pages.append({
        'loc': 'https://audiosnipt.com/',
        'lastmod': datetime.now().strftime('%Y-%m-%d'),
        'changefreq': 'daily',
        'priority': '1.0'
    })
    
    # Add blog pages
    pages.append({
        'loc': 'https://audiosnipt.com/blog',
        'lastmod': datetime.now().strftime('%Y-%m-%d'),
        'changefreq': 'weekly',
        'priority': '0.8'
    })
    
    # Add sample blog posts
    blog_posts = [
        {
            'slug': 'how-to-find-quotes-in-youtube-videos',
            'date': '2024-01-20'
        },
        {
            'slug': 'best-practices-for-content-research',
            'date': '2024-01-19'
        }
    ]
    
    for post in blog_posts:
        pages.append({
            'loc': f'https://audiosnipt.com/blog/{post["slug"]}',
            'lastmod': post['date'],
            'changefreq': 'monthly',
            'priority': '0.7'
        })
    
    # Create the sitemap XML
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += (
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    )
    
    for page in pages:
        xml_content += '  <url>\n'
        xml_content += f'    <loc>{page["loc"]}</loc>\n'
        xml_content += f'    <lastmod>{page["lastmod"]}</lastmod>\n'
        xml_content += f'    <changefreq>{page["changefreq"]}</changefreq>\n'
        xml_content += f'    <priority>{page["priority"]}</priority>\n'
        xml_content += '  </url>\n'
    
    xml_content += '</urlset>'
    
    return Response(
        response=xml_content,
        status=200,
        mimetype='application/xml'
    ) 