"""Visualisation utilities."""

import numpy as np
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from shapely.geometry import Polygon
from shapely.ops import cascaded_union

from ..utils import clip_utils
from ..utils import las_utils
from ..utils import bgt_utils
from ..utils.labels import Labels


bgt_labels = {'boom': 'Tree',
              'lichtmast': 'Lamp post',
              'verkeersbord': 'Traffic sign',
              'pand': 'Building',
              'wegdeel': 'Road'}
bgt_colors = {'boom': 'green',
              'lichtmast': 'orange',
              'verkeersbord': 'darkviolet',
              'pand': 'lightblue',
              'pand_poly': 'royalblue',
              'wegdeel': 'lightgrey'}
cloud_colors = {'Unlabelled': 'lightgrey',
                'Ground': 'peru',
                'Building': 'lightblue',
                'Tree': 'green',
                'Street light': 'orange',
                'Traffic sign': 'darkviolet',
                'Traffic light': 'red',
                'Car': 'grey',
                'Noise': 'whitesmoke'}


def plot_cloud_slice(las_file, ahn_reader, plane_height=1.5, hide_noise=False,
                     ax=None, title=None, legend_below=False):
    full_plot = False
    if ax is None:
        fig, ax = plt.subplots(1, constrained_layout=True)
        full_plot = True

    las = las_utils.read_las(las_file)
    labels = las.label
    points = np.vstack((las.x, las.y, las.z)).T

    tilecode = las_utils.get_tilecode_from_filename(las_file)
    ((x_min, y_max), (x_max, y_min)) =\
        las_utils.get_bbox_from_tile_code(tilecode)

    points_z = ahn_reader.interpolate(tilecode, points,
                                      np.ones((len(points),), dtype=bool),
                                      'ground_surface')

    plane_mask = ((points[:, 2] >= points_z + plane_height - 0.05)
                  & (points[:, 2] <= points_z + plane_height + 0.05))
    label_set = np.unique(labels[plane_mask])

    for label in label_set:
        if label == Labels.NOISE and hide_noise:
            continue
        label_mask = plane_mask & (labels == label)
        label_str = Labels.get_str(label)
        ax.scatter(points[label_mask, 0], points[label_mask, 1],
                   c=cloud_colors[label_str], marker='.', label=label_str)

    box = patches.Rectangle((x_min, y_min), x_max-x_min, y_max-y_min,
                            linewidth=1, linestyle='--', edgecolor='black',
                            fill=False)
    ax.add_patch(box)

    if title is not None:
        ax.set_title(title)
    ax.set_xlabel('X')
    ax.set_xticks(range(x_min, x_max+1, 10))
    ax.set_xticklabels(range(x_min, x_max+1, 10))
    ax.set_ylabel('Y')
    ax.set_yticks(range(y_min, y_max+1, 10))
    ax.set_yticklabels(range(y_min, y_max+1, 10))
    if not legend_below:
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    else:
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)
    ax.set_aspect('equal', adjustable='box')
    if full_plot:
        plt.show()


def plot_bgt(tilecode, building_file=None, road_file=None, point_file=None,
             ax=None, title=None, show_legend=True, legend_below=False):
    padding = 2.5

    full_plot = False
    if ax is None:
        width = 7 if show_legend else 5
        fig, ax = plt.subplots(1, figsize=(width, 5), constrained_layout=True)
        full_plot = True

    if title is None:
        title = f'BGT tile {tilecode}'

    buildings = []
    roads = []
    points = []

    if building_file:
        buildings = bgt_utils.get_polygons(building_file, tilecode)
    if road_file:
        roads = bgt_utils.get_polygons(road_file, tilecode)
    if point_file:
        points = bgt_utils.get_points(point_file, tilecode, padding=padding)

    ((x_min, y_max), (x_max, y_min)) =\
        las_utils.get_bbox_from_tile_code(tilecode)

    for poly in [Polygon(bld) for bld in buildings]:
        x, y = poly.exterior.xy
        ax.fill(x, y, c=bgt_colors['pand'], label=bgt_labels['pand'])
        ax.plot(x, y, c=bgt_colors['pand_poly'])

    for poly in [Polygon(rd) for rd in roads]:
        x, y = poly.exterior.xy
        ax.fill(x, y, c=bgt_colors['wegdeel'], label=bgt_labels['wegdeel'])

    for pt in points:
        ax.scatter(pt[1], pt[2],
                   c=bgt_colors[pt[0]], marker='x', label=bgt_labels[pt[0]])

    box = patches.Rectangle((x_min, y_min), x_max-x_min, y_max-y_min,
                            linewidth=1, linestyle='--', edgecolor='black',
                            fill=False)
    ax.add_patch(box)

    ax.set_title(title)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')

    if show_legend:
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        if not legend_below:
            ax.legend(by_label.values(), by_label.keys(),
                      loc='center left', bbox_to_anchor=(1, 0.5))
        else:
            ax.legend(by_label.values(), by_label.keys(),
                      loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)

    ax.set_xticks(range(x_min, x_max+1, 10))
    ax.set_xticklabels(range(x_min, x_max+1, 10))
    ax.set_yticks(range(y_min, y_max+1, 10))
    ax.set_yticklabels(range(y_min, y_max+1, 10))

    ax.set_xlim((x_min - padding, x_max + padding))
    ax.set_ylim((y_min - padding, y_max + padding))
    ax.set_aspect('equal', adjustable='box')
    if full_plot:
        plt.show()


def plot_bgt_and_cloudslice(tilecode, las_file, ahn_reader,
                            building_file=None, road_file=None,
                            point_file=None, plane_height=1.5,
                            hide_noise=False):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5.5))
    plot_bgt(tilecode, building_file, road_file, point_file,
             title='BGT data', ax=ax1, legend_below=True)
    plot_cloud_slice(las_file, ahn_reader, plane_height=plane_height,
                     hide_noise=hide_noise, title='LAS labels', ax=ax2,
                     legend_below=True)
    ax2.set_yticklabels([])
    ax2.yaxis.label.set_visible(False)
    fig.suptitle(f'Tile {tilecode}', fontsize=14)
    fig.subplots_adjust(top=0.95)
    plt.show()


def plot_ahn_surface(ahn_tile, surf='ground_surface', ax=None, cbar_pad=0.04):
    cmap = {'ground_surface': 'gist_earth',
            'building_surface': 'Oranges'}
    cbar_title = {'ground_surface': 'Ground elevation (m)',
                  'building_surface': 'Building height (m)'}
    full_plot = False
    if ax is None:
        full_plot = True
        fig, ax = plt.subplots(1)

    x_min = int(ahn_tile['x'][0])
    x_max = int(np.ceil(ahn_tile['x'][-1]))
    y_min = int(ahn_tile['y'][-1])
    y_max = int(np.ceil(ahn_tile['y'][0]))

    im = ax.imshow(ahn_tile[surf], extent=[x_min, x_max, y_min, y_max],
                   interpolation='none', cmap=cmap[surf])

    ax.set_title(surf)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_xticks(range(x_min, x_max+1, 10))
    ax.set_xticklabels(range(x_min, x_max+1, 10))
    ax.set_yticks(range(y_min, y_max+1, 10))
    ax.set_yticklabels(range(y_min, y_max+1, 10))
    cbar = plt.colorbar(im, ax=[ax], fraction=0.046, pad=cbar_pad)
    cbar.ax.set_ylabel(cbar_title[surf], rotation=270, labelpad=10)
    if full_plot:
        plt.show()


def plot_ahn_sidebyside(tilecode, ahn_reader):
    ahn_tile = ahn_reader.filter_tile(tilecode)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
    plot_ahn_surface(ahn_tile, surf='ground_surface', ax=ax1)
    plot_ahn_surface(ahn_tile, surf='building_surface', ax=ax2)
    ax2.set_yticklabels([])
    ax2.yaxis.label.set_visible(False)
    fig.suptitle(f'AHN tile {tilecode}', fontsize=14)
    plt.show()


def plot_ahn_merged(tilecode, ahn_reader):
    ahn_tile = ahn_reader.filter_tile(tilecode)
    fig, ax1 = plt.subplots(1, figsize=(7, 5))
    plot_ahn_surface(ahn_tile, surf='ground_surface', ax=ax1, cbar_pad=0.14)
    plot_ahn_surface(ahn_tile, surf='building_surface', ax=ax1, cbar_pad=0.04)
    ax1.set_title(f'AHN tile {tilecode}', fontsize=14)
    plt.show()


def plot_buildings_ahn_bgt(tilecode, ahn_reader, building_file, offset=1,
                           show_elevation=True, offset_only=True, title=None):
    ahn_tile = ahn_reader.filter_tile(tilecode)
    buildings = bgt_utils.get_polygons(building_file, tilecode)
    if offset > 0:
        buildings_ofs = list(cascaded_union(
            [Polygon(clip_utils.poly_offset(bld, offset))
             for bld in buildings]))
    else:
        buildings_ofs = []
    ((x_min, y_max), (x_max, y_min)) =\
        las_utils.get_bbox_from_tile_code(tilecode)

    fig, ax = plt.subplots(1, figsize=(7, 5), constrained_layout=True)

    if show_elevation:
        plot_ahn_surface(
            ahn_tile, surf='building_surface', ax=ax, cbar_pad=0.04)
        if title is None:
            title = 'Building footprints and elevation'
    else:
        cmap = mcolors.LinearSegmentedColormap.from_list('sg', ['lightgrey']*2)
        ax.imshow(ahn_tile['building_surface'],
                  extent=[x_min, x_max, y_min, y_max],
                  interpolation='none', cmap=cmap)
        dummy = patches.Patch(color='lightgrey', label='AHN surface')
        if title is None:
            title = 'Building footprints'

    if not offset_only:
        for poly in [Polygon(bld) for bld in buildings]:
            x, y = poly.exterior.xy
            ax.plot(x, y, c=bgt_colors['pand_poly'], label='BGT polygon')
    for poly in buildings_ofs:
        x, y = poly.exterior.xy
        ax.plot(x, y, c=bgt_colors['pand_poly'], linestyle='--',
                label='Offset polygon')

    box = patches.Rectangle((x_min, y_min), x_max-x_min, y_max-y_min,
                            linewidth=1, linestyle='--', edgecolor='black',
                            fill=False)
    ax.add_patch(box)

    ax.set_title(title)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_xticks(range(x_min, x_max+1, 10))
    ax.set_xticklabels(range(x_min, x_max+1, 10))
    ax.set_yticks(range(y_min, y_max+1, 10))
    ax.set_yticklabels(range(y_min, y_max+1, 10))

    if not show_elevation:
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        by_label[dummy.get_label()] = dummy
        ax.legend(by_label.values(), by_label.keys(),
                  loc='center left', bbox_to_anchor=(1, 0.5))

    padding = 2.5
    ax.set_xlim((x_min - padding, x_max + padding))
    ax.set_ylim((y_min - padding, y_max + padding))
    ax.set_aspect('equal', adjustable='box')
    plt.show()
