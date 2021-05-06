import torch
from network.network import Network
from run.train import train, LATEST_CHKPT_PATH
import coloredlogs
coloredlogs.install(level='INFO', fmt='%(asctime)s %(name)s %(levelname)s %(message)s')

if __name__ == '__main__':
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    T = 8
    max_time_s = 5
    start_fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
    net = train(
        T,
        device=device,
        start_fen=start_fen,
        max_time_s=max_time_s,
        num_games=100,
        chkpt_path=f'checkpoints/{LATEST_CHKPT_PATH}'
    )
