from typing import Dict, Optional, Union

import torch
import torch.nn as nn


class CRNN(nn.Module):
    def __init__(
        self,
        num_classes: int,
        image_height: int = 32,
        hidden_size: int = 256,
        num_layers: int = 2,
        dropout: float = 0.1
    ):
        super(CRNN, self).__init__()

        assert image_height % 16 == 0, "image_height must be a multiple of 16"

        self.cnn = nn.Sequential(
            nn.Conv2d(1, 64, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),

            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),

            nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),

            nn.Conv2d(256, 256, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(2, 1), stride=(2, 1)),

            nn.Conv2d(256, 512, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),

            nn.Conv2d(512, 512, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(2, 1), stride=(2, 1)),

            nn.Conv2d(512, 512, kernel_size=2, stride=1, padding=0),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
        )

        self.map_to_sequence = nn.Linear(512 * (image_height // 16 - 1), hidden_size)

        self.rnn = nn.LSTM(
            input_size=hidden_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0
        )

        self.fc = nn.Linear(hidden_size * 2, num_classes)

    def forward(
        self,
        x: torch.Tensor,
        return_intermediates: bool = False
    ) -> Union[torch.Tensor, Dict[str, torch.Tensor]]:
        spatial_feat: Optional[torch.Tensor] = None
        for i, layer in enumerate(self.cnn):
            x = layer(x)
            if return_intermediates and i == 11:
                spatial_feat = x.detach().clone()

        conv = x
        batch_size, channels, height, width = conv.size()

        conv = conv.permute(0, 3, 1, 2)
        conv = conv.contiguous().view(batch_size, width, -1)

        sequence = self.map_to_sequence(conv)

        recurrent, _ = self.rnn(sequence)

        output = self.fc(recurrent)
        output = output.log_softmax(dim=2)

        if return_intermediates:
            return {
                "output": output,
                "spatial": spatial_feat if spatial_feat is not None else conv.detach(),
                "seq_len": width,
            }
        return output
