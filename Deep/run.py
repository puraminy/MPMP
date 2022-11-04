import torch
from model import PretrainPrompt
from trainer import MutitaskTrainer
from dataload import *
import torch
import argparse
from torch.optim import AdamW
import os


parser = argparse.ArgumentParser()
parser.add_argument("--n_prompt_tokens", default=10, type=int)
parser.add_argument("--intrinsic_dim", default=300, type=int)
parser.add_argument("--save_every", default=10000, type=int)
parser.add_argument("--batch_size", default=2, type=int)
parser.add_argument("--n_steps", default=1000, type=int)
parser.add_argument("--print_every", default=2000, type=int)
parser.add_argument("--eval_every", default=500, type=int)
parser.add_argument("--device", default='cuda:0', type=str)
parser.add_argument("--n_prompts", default=8, type=int)
parser.add_argument("--seed", default=42, type=int)
parser.add_argument("--lr_router", default=.0005, type=float)
parser.add_argument("--lr_prompt", default=.0001, type=float)
parser.add_argument("--anneal_rate", default=None, type=float)
parser.add_argument("--anneal_min", default=None, type=float)
parser.add_argument("--init_temperature", default=1., type=float)
parser.add_argument("--step_size1", default=None, type=int)
parser.add_argument("--step_size2", default=1000, type=int)
parser.add_argument("--gamma1", default=.1, type=float)
parser.add_argument("--gamma2", default=.1, type=float)
parser.add_argument("--accumulation_step", default=1, type=int)
parser.add_argument("--model_path", default="bert-base-cased", type=str)
args = parser.parse_args()


class Optim:
    def __init__(self, para1, para2, lr1, lr2):
        self.optimizer1 = AdamW(para1, lr=lr1, betas=(0.9, 0.999))
        self.optimizer2 = AdamW(para2, lr=lr2, betas=(0.9, 0.999))

    def step(self):
        self.optimizer1.step()
        self.optimizer2.step()

    def zero_grad(self):
        self.optimizer1.zero_grad()
        self.optimizer2.zero_grad()

    def state_dict(self):
        return {
            'optimizer1': self.optimizer1.state_dict(),
            'optimizer2': self.optimizer2.state_dict()
        }

    def load_state_dict(self, state_dict):
        self.optimizer1.load_state_dict(state_dict['optimizer1'])
        self.optimizer2.load_state_dict(state_dict['optimizer2'])

    def cuda(self):
        for state in self.optimizer1.state.values():
            for k, v in state.items():
                if isinstance(v, torch.Tensor):
                    state[k] = v.cuda()

        for state in self.optimizer2.state.values():
            for k, v in state.items():
                if isinstance(v, torch.Tensor):
                    state[k] = v.cuda()

class Scheduler:
    def __init__(self, optim, step1=10000, step2=10000, gamma1=.1, gamma2=.1):
        self.scheduler1 = torch.optim.lr_scheduler.StepLR(optim.optimizer1, step1, gamma1)
        self.scheduler2 = torch.optim.lr_scheduler.StepLR(optim.optimizer2, step2, gamma2)

    def step(self):
        self.scheduler1.step()
        self.scheduler2.step()


save_path = f'./results/PromptTokens{args.n_prompt_tokens}_BatchSize{args.batch_size}_NPrompts{args.n_prompts}_LrRouter{args.lr_router}_LrPrompt{args.lr_prompt}_AnnealParams{args.init_temperature};{args.anneal_rate};{args.anneal_min}'
if not os.path.exists(save_path):
    os.makedirs(save_path, exist_ok=True)
args.save_path = save_path
torch.manual_seed(args.seed)

#model_path = args.model_path
model_path = "/home/pouramini/pret/bert"
model = PretrainPrompt(args.intrinsic_dim, args.n_prompt_tokens, num_datasets, args.n_prompts, args.init_temperature, model_path=model_path)

optimizer = Optim(
    [model.model.model.encoder.encoder.router],
    [
        model.model.model.encoder.encoder.A,
        model.model.model.encoder.encoder.z,
        model.model.qa_outputs.weight
    ],
    args.lr_router,
    args.lr_prompt
)
if args.step_size1 is not None and args.step_size2 is not None and args.gamma1 is not None and args.gamma2 is not None:
    scheduler = Scheduler(optimizer, args.step_size1, args.step_size2, args.gamma1, args.gamma2)
else:
    scheduler = None



trainer = MutitaskTrainer(args, model, optimizer, scheduler)
#trainer = MutitaskTrainer.from_checkpoint(args, model, Optim, 700000)
trainer.train()
