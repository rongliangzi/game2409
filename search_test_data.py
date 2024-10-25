# brute search data as test set
def dfs(grid, loc, cur_path, cur_cost, not_collect_first):
    # search for grid where not collect when first arrival in best_path 
    pass


def random_init_search(size, cls_n, elim_n):
    grid, loc = init_grid_loc(size, cls_n, elim_n)
    best_path, cost, exist = dfs(grid, loc, [], 0, False)
    if exist:
        save(grid, loc, best_path, cost)


if __name__ == "__main__":
    for _ in range(10):
        random_init_search(size, cls_n, elim_n)
