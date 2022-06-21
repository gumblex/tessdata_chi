#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import sys
import gzip
import random
import sqlite3
import itertools
import collections

#os.environ["OMP_NUM_THREADS"] = "1"
#os.environ["OPENBLAS_NUM_THREADS"] = "1"
#os.environ["MKL_NUM_THREADS"] = "1"
#os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
#os.environ["NUMEXPR_NUM_THREADS"] = "1"

import umap
import numpy as np
import sklearn.cluster


random.seed(64)

MAX_CHAR = 50
DIMENSION = 4
NUM_CODE = 26


CJK_RANGES = (
    (0x2E80, 0x2EFF),  # CJK Radicals Supplement
    (0x2F00, 0x2FDF),  # Kangxi Radicals
    (0x31C0, 0x31EF),  # CJK Strokes
    (0x3400, 0x4DBF),  # CJK Unified Ideographs Extension A
    (0x4E00, 0x9FFF),  # CJK Unified Ideographs
    (0x20000, 0x2A6DF),  # CJK Unified Ideographs Extension B
    (0x2A700, 0x2B73F),  # CJK Unified Ideographs Extension C
    (0x2B740, 0x2B81F),  # CJK Unified Ideographs Extension D
    (0x2B820, 0x2CEAF),  # CJK Unified Ideographs Extension E
    (0x2CEB0, 0x2EBEF),  # CJK Unified Ideographs Extension F
    (0x30000, 0x3134F),  # CJK Unified Ideographs Extension G
)


def transform_cjk_label(code: int):
    # code = ord(char)
    label = 0
    for x, y in CJK_RANGES:
        if x <= code <= y:
            label += code - x
            break
        label += y - x + 1
    return label


def save_arr(cur, name, data):
    buf = io.BytesIO()
    np.save(buf, data)
    cur.execute("INSERT INTO train_data VALUES (?,?)",
        (name, gzip.compress(buf.getvalue())))


def load_arr(cur, name):
    row = cur.execute("SELECT data FROM train_data WHERE name=?", (name,)).fetchone()
    if row is None:
        raise KeyError(name)
    buf = io.BytesIO(gzip.decompress(row[0]))
    return np.load(buf)


def img_reduce_dim(cur):
    print("Load images...", file=sys.stderr)
    cur.execute("""
        SELECT font, count(DISTINCT ch) num
        FROM char_image
        GROUP BY font ORDER BY num DESC
    """)
    fonts = {}
    for font, num in cur:
        fonts[font] = num
    cur.execute("""
        SELECT ch, font, img FROM char_image ORDER BY ch, font
    """)
    buf = io.BytesIO()
    labels = []
    for char, group in itertools.groupby(cur, key=lambda x: x[0]):
        imgs = [row[1:] for row in group]
        if len(imgs) > MAX_CHAR:
            imgs.sort(key=lambda x: fonts[x[0]], reverse=True)
            imgs_a = imgs[:MAX_CHAR//2]
            imgs_b = imgs[MAX_CHAR//2:]
            random.shuffle(imgs_b)
            imgs = imgs_a + imgs_b[:(MAX_CHAR-len(imgs_a))]
        for row in imgs:
            buf.write(row[1])
            labels.append(ord(char))
    arr = np.frombuffer(buf.getvalue(), dtype='u1').reshape((len(labels), 24*24))
    labels_y = np.array(list(map(transform_cjk_label, labels)))
    print(arr.shape, len(labels), file=sys.stderr)
    del buf
    print("UMAP...", file=sys.stderr)
    um = umap.UMAP(
        n_neighbors=min(MAX_CHAR, 50), n_components=DIMENSION, min_dist=0.1,
        n_epochs=500, low_memory=True, verbose=True)
    arr4 = um.fit_transform(arr, y=labels_y)
    return arr4, np.array(labels, dtype='i4')


def kmeans_optimize(dbname):
    db = sqlite3.connect(dbname)
    cur = db.cursor()
    print('Reduce dim...')
    cur.execute("CREATE TABLE IF NOT EXISTS train_data ("
        "name TEXT PRIMARY KEY,"
        "data BLOB"
    ")")
    try:
        arr4 = load_arr(cur, 'train_x_%dd' % DIMENSION)
        labels = load_arr(cur, 'train_y')
    except KeyError:
        arr4, labels = img_reduce_dim(cur)
        save_arr(cur, 'train_x_%dd' % DIMENSION, arr4)
        save_arr(cur, 'train_y', labels)
        db.commit()

    print(arr4.shape, arr4.dtype)
    print('KMeans...')
    kmeans = sklearn.cluster.BisectingKMeans(
        n_clusters=NUM_CODE**3,
        n_init=10, random_state=10,
        bisecting_strategy='largest_cluster')  #, verbose=1)
    # kmeans = sklearn.cluster.MiniBatchKMeans(
        #n_clusters=NUM_CODE**3, init='random',
        #batch_size=2*NUM_CODE**3, n_init=10,
        #max_no_improvement=50, compute_labels=False, verbose=2)
    # kmeans = sklearn.cluster.KMeans(
        # n_clusters=NUM_CODE**3, init='random', verbose=2)

    kmeans.fit(arr4)
    centers = kmeans.cluster_centers_

    print('Cluster mean...')
    char_centroid = {}
    char_cluster_map = [list() for x in centers]
    for char, group in itertools.groupby(zip(labels, arr4), key=lambda x: x[0]):
        char_vec = np.array([row for label, row in group])
        distance = np.mean(kmeans.transform(char_vec), axis=0)
        cluster = np.argmin(distance)
        if char in char_centroid:
            print(chr(char))
        char_centroid[char] = np.median(char_vec, axis=0)
        char_cluster_map[cluster].append(char)
    remaining_cluster = np.ones((len(char_cluster_map),), dtype=bool)
    while np.sum(remaining_cluster) > 0:
        cluster = max(
            np.nonzero(remaining_cluster)[0],
            key=lambda x: len(char_cluster_map[x]))
        if len(char_cluster_map[cluster]) <= NUM_CODE:
            break
        print(cluster, len(char_cluster_map[cluster]))
        remaining_cluster[cluster] = False
        remaining_cluster_idx = np.nonzero(remaining_cluster)[0]
        # rearranged.add(cluster)
        distance = kmeans.transform(
            [char_centroid[char] for char in char_cluster_map[cluster]])
        char_order = []
        for i, char in sorted(enumerate(char_cluster_map[cluster]),
            key=lambda x: distance[x[0], cluster]):
            next_cluster = remaining_cluster_idx[
                np.argmin(distance[i,remaining_cluster])]
            char_order.append((char, next_cluster, distance[i,next_cluster]))
        del distance
        char_cluster_map[cluster] = [row[0] for row in char_order[:NUM_CODE]]
        for char, next_cluster, dist in char_order[NUM_CODE:]:
            char_cluster_map[next_cluster].append(char)
            print(' %s %d -> %d (%s), %.2f' % (
                chr(char), cluster, next_cluster,
                chr((char_cluster_map[next_cluster] or [''])[0]), dist))

    print('Generate code...')
    cluster_index = list(range(centers.shape[0]))
    for dim in range(3):
        cluster_index = [x[1] for x in sorted(
            enumerate(cluster_index),
            key=lambda x: (x[0] // (NUM_CODE**(3-dim)), centers[x[1], dim])
        )]
    cluster_code = [None] * centers.shape[0]
    for i, cluster in enumerate(cluster_index):
        code = []
        c1 = i
        for dim in range(3):
            c1, rem = divmod(c1, NUM_CODE)
            code.append(rem)
        cluster_code[cluster] = tuple(code)

    dim4_clusters = {char: i / (len(char_centroid) / NUM_CODE)
        for i, char in enumerate(sorted(
            char_centroid.keys(), key=lambda x: char_centroid[x][-1]))}

    char_code = {}
    print('char_code...')
    for cluster, chars in enumerate(char_cluster_map):
        char_pos = [list() for x in range(NUM_CODE)]
        for n, char in sorted((dim4_clusters[char], char) for char in chars):
            char_pos[int(n)].append(char)
        carry = collections.deque()
        for n in range(len(char_pos)):
            if not carry and len(char_pos[n]) <= 1:
                continue
            carry.extend(char_pos[n])
            char_pos[n].clear()
            left_empty = [i for i in range(n) if len(char_pos[i]) == 0]
            used_num = min(len(carry)-1, len(left_empty))
            for i in reversed(left_empty[-used_num:]):
                del char_pos[i]
                char_pos.insert(n, [])
            for i in range(n-used_num, n+1):
                char_pos[i].append(carry.popleft())
        for i, bucket in enumerate(char_pos):
            if not bucket:
                continue
            code = list(cluster_code[cluster])
            code.append(i)
            char_code[bucket[0]] = tuple(x+1 for x in code)
    with open('chars_embedding_kmeans.txt', 'w', encoding='utf-8') as f:
        for char in sorted(char_code):
            print(' '.join(map(str, (char,) + char_code[char])), file=f)


if __name__ == '__main__':
    kmeans_optimize(sys.argv[1])
