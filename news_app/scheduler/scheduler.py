from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from django_apscheduler.jobstores import register_events, DjangoJobStore
import sys

from news_app.dto.news import NewsItem
from news_app.models import News
from news_app.services.classifier import Classifier
from news_app.services.spider import Spider
from news_app.services.hiru_spider import HiruSpider
from news_app.services.newsfirst_spider import NewsFirstSpider
from recommendation.services.vector_db_provider import get_chroma_db_collection
from sinhala_news_platform_backend.settings import NEWS_ABSTRACT_SIZE

def trigger_web_spider(scheduler):

    # Get all jobs
    jobs = scheduler.get_jobs()
    
    # Print job IDs and the number of jobs
    for job in jobs:
        print(f'Job ID: {job.id}')
    print(f'Number of current jobs: {len(jobs)}')


    print("trigger_web_spider task is running...")

    classifier = Classifier()
    chroma_collection = get_chroma_db_collection()

    spiders = [Spider(), HiruSpider(), NewsFirstSpider()]
    news_items: list[NewsItem] = []
    for spider in spiders:
        try:
            news_items.extend(spider.load_latest_news_items())
        except Exception as e:
            print(f'{type(spider).__name__} failed to load news items: {e}')

    classified_news_items: list[NewsItem] = classifier.bert_classify(news_items)

    for classifed_news_item in classified_news_items:

        print(f'Saving news id: {classifed_news_item.news_id}, Category: {classifed_news_item.category}')

        news_model, created = News.objects.get_or_create(
            news_id=classifed_news_item.news_id,
            defaults=dict(
                date=classifed_news_item.timestamp,
                heading=classifed_news_item.heading,
                category=classifed_news_item.category,
                link_to_source=classifed_news_item.link_to_source,
                abstract=classifed_news_item.content[:NEWS_ABSTRACT_SIZE]
            )
        )

        if not created:
            # Already saved (e.g. by an overlapping run) -- its embedding
            # was already added too, so skip re-adding to Chroma.
            continue

        chroma_collection.add(
            ids=[classifed_news_item.news_id],
            embeddings=[classifed_news_item.get_content_embedding()],
            metadatas=[{'timestamp': classifed_news_item.get_posix_timstamp()}]
        )

        
    
    print('trigger_web_spider task completed')

def start():

    # 10 seconds delay to start the scheduler after app is started
    # time.sleep(10)
    

    scheduler = BackgroundScheduler(
        gconfig = {
            'apscheduler.job_defaults.max_instances': 1
        }
    )
    # scheduler.add_jobstore(DjangoJobStore(), "default")
    # scheduler.add_jobstore(MemoryJobStore(), 'inmemory')
    print(f'Current jobs: {scheduler.get_jobs()}')

    if scheduler.running:
        scheduler.shutdown(False)
        scheduler.start(False)
    
    scheduler.remove_all_jobs()
    scheduler.add_job(trigger_web_spider, 
                      'interval', 
                      seconds=300, 
                      name='my_task_1', 
                    #   jobstore='inmemory',
                      max_instances=1,
                      args=[scheduler]
                      )
    register_events(scheduler)
    scheduler.start()
    print("Scheduler started...", file=sys.stdout)
