from .mask_policy import square_move_to_index
from utils import square_to_n_n
import chess
import torch

class MCTSDist:
    '''
        The information from the MCTS distribution obtained from the root
        to be stored in the replay memory.
    '''
    def __init__(self, root):
        self.fen = root.fen
        self.value = root.get_state_value()
        self.move_data = [MoveData(edge) for edge in root.out_edges]

class MCTSPolicyEncoder:
    def __init__(self, temp=2):
        self.temp = temp

    def get_mcts_policy(self, mcts_dist):
        '''
            Takes the MCTSDist and converts it to a gold
            distribution in the shape of the network's policy.
        '''
        policy = torch.zeros(8,8,73)

        for move in mcts_dist.move_data:
            row, col = square_to_n_n(move.from_square)
            index = square_move_to_index(move.from_square, move.to_square, move.promotion)
            score = move.n_visits ** (1 / self.temp)

            policy[row,col,index] = score

        policy /= policy.sum()
        return policy

class MoveData:
    def __init__(self, tree_edge):
        move = chess.Move.from_uci(tree_edge.uci)

        self.from_square = move.from_square
        self.to_square = move.to_square
        self.promotion = move.promotion
        self.n_visits = tree_edge.n_visits