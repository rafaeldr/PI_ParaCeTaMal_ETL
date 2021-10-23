import pandas as pd
#import cairocffi
import igraph as ig
import zipfile

zip_edges = r"..\DataSources\edges.zip"

with zipfile.ZipFile(zip_edges) as z:
    with z.open("edges.csv") as f:
        net_edges = pd.read_csv(f, header=0)
        drug_graph = ig.Graph.DataFrame(net_edges, directed=False)

ig.plot(drug_graph)

pass