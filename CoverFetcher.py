#!/usr/bin/env python3
import urllib3
import certifi
from queue import Queue
from threading import Thread
import urllib.parse
import json
import os
import colorama
import logging

logger = logging.getLogger('CoverFetcher')


class CoverFetcher:
    def __init__(self, dict_missing_cover_directories, i_max_concurrent_jobs=5):

        self.i_max_jobs = i_max_concurrent_jobs
        self.conn = urllib3.PoolManager(num_pools=self.i_max_jobs, cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())

        self.q_objects_to_process = Queue(maxsize=0)
        for s_current_directory in dict_missing_cover_directories.keys():
            self.q_objects_to_process.put([dict_missing_cover_directories[s_current_directory][0], dict_missing_cover_directories[s_current_directory][1], s_current_directory])

        self.params = {
            'format': 'json',
            'method': 'album.getInfo',
            'api_key': "a42ead6d2dcc2938bec2cda08a03b519",
            'artist': '',
            'album': ''
        }

        self.SEARCH_URL = "https://ws.audioscrobbler.com/2.0/?"

        self.l_threads = []

    def go_fetch(self):
        for i_thread_count in range(self.i_max_jobs):
            thr_current_worker = Thread(target=self.thread_process, args=(self.q_objects_to_process,))
            thr_current_worker.setDaemon(True)
            thr_current_worker.start()
            self.l_threads.append(thr_current_worker)

        # block until all tasks are done
        self.q_objects_to_process.join()

        # stop workers
        for i_thread_count in range(self.i_max_jobs):
            self.q_objects_to_process.put(None)
        for thr_current_thread in self.l_threads:
            thr_current_thread.join()


    def thread_process(self, q_current_queue):
        while True:
            l_current_queue_element = q_current_queue.get()
            if l_current_queue_element is None:
                break
            print(colorama.Fore.GREEN + 'OUT: processing artist "{}", album "{}"'.format(*l_current_queue_element))
            self.save(*l_current_queue_element)
            q_current_queue.task_done()

    @staticmethod
    def _fetchimage(jsonobj, size):
        if 'album' in jsonobj and 'image' in jsonobj['album']:
            for elt in jsonobj['album']['image']:
                if elt['size'] == size:
                    return elt['#text'] if '#text' in elt and elt['#text'] != '' else None
        return None

    def save(self, artist, album, target_directory):
        url = self.search(artist, album)
        if url is not None:
            try:
                image_file_descriptor = self.conn.request('GET', url)
                _, file_extension = os.path.splitext(url)
                if image_file_descriptor is not None:
                    s_cover_image_file_name = target_directory + '/cover' + file_extension
                    with open(s_cover_image_file_name, 'wb') as image_file_out:
                        image_file_out.write(image_file_descriptor.data)
                    print(colorama.Fore.GREEN + 'OUT: cover image saved to file ' + s_cover_image_file_name)

                return True
            except:
                logger.exception('Error while fetching album cover')
                return None
        else:
            return None

    def search(self, artist, album):
        self.params['artist'] = artist
        self.params['album'] = album
        params = urllib.parse.urlencode(self.params)
        url = self.SEARCH_URL + params
        try:
            r = self.conn.request('GET', url)
            return self._fetchimage(json.loads(r.data.decode('utf-8')), 'extralarge')
        except:
            logger.exception('Error while searching album cover')
            return None



if __name__ == "__main__":
    cu = CoverFetcher()
    print(cu.search('Dagoba', 'Tales of the Black Dawn'))
