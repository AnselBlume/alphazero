import torch
import torch.nn as nn
from torch.optim import Adam
from network.network import Network
from network.loss import MCTSLoss
from .play import GameRunner, START_FEN
from .replay_mem import ReplayMemory
import os
import logging
import wandb

wandb.init(project='alphazero', entity='blume5', reinit=True)
logger = logging.getLogger(__name__)

GAMES_TRAINED_KEY = 'games_trained'
MODEL_KEY = 'model_state_dict'
OPTIMIZER_KEY = 'optimizer_state_dict'
REPLAY_MEM_KEY = 'replay_mem'

CHECKPOINT_DIR = 'checkpoints'
LATEST_CHKPT_PATH = 'latest_chkpt.tar'
CHKPT_NUM_FMT = 'chkpt_%d.tar'

def train(T, device='cpu', num_games=10, chkpt_path=None, start_fen=START_FEN,
          max_time_s=30):
    net, optimizer, games_trained, replay_mem = load_state(T, chkpt_path, device)
    wandb.watch(net, log_freq=50)

    game_runner = GameRunner(T, device=device, max_time_s=max_time_s)
    mcts_loss = MCTSLoss(T, device=device)

    for game_num in range(games_trained + 1, num_games + games_trained + 1):
        logger.info(f'Starting self-play game {game_num}')
        board, mcts_dist_histories = game_runner.play_game(net, start_fen=start_fen)
        logger.info(f'Completed self-play game {game_num}')

        logger.info(f'Saving replay memory')
        replay_mem.save(mcts_dist_histories)
        save_state(net, optimizer, games_trained, replay_mem, LATEST_CHKPT_PATH)

        logger.info(f'Performing gradient step')
        mcts_dist_histories = replay_mem.sample()

        net.train() # game_runner sets the network to eval
        optimizer.zero_grad()
        loss = mcts_loss.get_loss(net, mcts_dist_histories)
        loss.backward()
        wandb.log({
            'Loss' : loss.item(),
            'Games trained' : games_trained
        })
        optimizer.step()

        logger.info(f'Saving updated network')
        games_trained += 1
        save_state(net, optimizer, games_trained, replay_mem, LATEST_CHKPT_PATH)

        if game_num == 1 or game_num % 5 == 0:
            save_state(net, optimizer, games_trained, replay_mem, CHKPT_NUM_FMT % game_num)

def save_state(net, optimizer, games_trained, replay_mem, chkpt_path):
    if not os.path.exists(CHECKPOINT_DIR):
        os.mkdir(CHECKPOINT_DIR)

    torch.save({
        GAMES_TRAINED_KEY: games_trained,
        MODEL_KEY: net.state_dict(),
        OPTIMIZER_KEY: optimizer.state_dict(),
        REPLAY_MEM_KEY: replay_mem
    }, os.path.join(CHECKPOINT_DIR, chkpt_path))

def load_state(T, chkpt_path, device):
    net = Network(T).to(device)
    optimizer = Adam(net.parameters(), weight_decay=1e-4)

    if chkpt_path is not None:
        checkpoint = torch.load(chkpt_path)
        net.load_state_dict(checkpoint[MODEL_KEY])
        optimizer.load_state_dict(checkpoint[OPTIMIZER_KEY])
        games_trained = checkpoint[GAMES_TRAINED_KEY]
        replay_mem = checkpoint[REPLAY_MEM_KEY]
    else:
        games_trained = 0
        replay_mem = ReplayMemory()

    return net, optimizer, games_trained, replay_mem

def save_checkpoint(path, save_dict):
    torch.save(save_dict, path)