"""
    Copyright 2023 Contributors

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

    This removes train/val/test masks on a dataset.
"""

import dgl
import os
import argparse

from remove_mask import print_feat_names

def remove_test_mask(data):
    new_data = {}
    for name in data:
        if 'test_mask' not in name:
            new_data[name] = data[name]
    return new_data

if __name__ == '__main__':
    argparser = argparse.ArgumentParser("Remove train/val/test masks")
    argparser.add_argument("--dataset", type=str, required=True,
                           help="The path to the partitioned graph.")
    argparser.add_argument("--remove_node_mask",
                           type=lambda x: (str(x).lower() in ['true', '1']), default=False,
                           help="Indicate to remove node masks or edge masks.")
    args = argparser.parse_args()

    print('before removing {} masks'.format('node' if args.remove_node_mask else 'edge'))
    print_feat_names(args.dataset)

    for d in os.listdir(args.dataset):
        part_dir = os.path.join(args.dataset, d)
        if not os.path.isfile(part_dir):
            if args.remove_node_mask:
                data = dgl.data.load_tensors(os.path.join(part_dir, 'node_feat.dgl'))
                data = remove_test_mask(data)
                dgl.data.save_tensors(os.path.join(part_dir, 'node_feat.dgl'), data)
            else:
                data = dgl.data.load_tensors(os.path.join(part_dir, 'edge_feat.dgl'))
                data = remove_test_mask(data)
                dgl.data.save_tensors(os.path.join(part_dir, 'edge_feat.dgl'), data)

    print('after removing {} test_masks'.format('node' if args.remove_node_mask else 'edge'))
    print_feat_names(args.dataset)
