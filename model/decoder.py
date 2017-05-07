import torch as t
import torch.nn as nn
import torch.nn.functional as F

from utils.functions import parameters_allocation_check


class Decoder(nn.Module):
    def __init__(self, params):
        super(Decoder, self).__init__()

        self.params = params

        self.rnn = nn.LSTM(input_size=self.params.latent_variable_size + self.params.word_embed_size,
                           hidden_size=self.params.decoder_size,
                           num_layers=self.params.decoder_num_layers,
                           batch_first=True)

        self.fc = nn.Linear(self.params.decoder_size, self.params.vocab_size)

    def forward(self, decoder_input, z, initial_state=None):
        """
        :param decoder_input: tensor with shape of [batch_size, seq_len, word_embed_size]
        :param z: latent variable with shape of [batch_size, latent_variable_size]
        :param initial_state: initial state of decoder rnn

        :return: unnormalized logits of sentense words distribution probabilities
                    with shape of [batch_size, seq_len, word_vocab_size]
                 final rnn state with shape of [num_layers, batch_size, decoder_rnn_size]
        """

        assert parameters_allocation_check(self), \
            'Invalid CUDA options. Parameters should be allocated in the same memory'

        [batch_size, seq_len, _] = decoder_input.size()

        '''decoder rnn is conditioned on context via additional bias = W_cond * z to every input token'''
        z = t.cat([z] * seq_len, 1).view(batch_size, seq_len, self.params.latent_variable_size)
        decoder_input = t.cat([decoder_input, z], 2)

        rnn_out, final_state = self.rnn(decoder_input, initial_state)

        rnn_out = rnn_out.contiguous().view(-1, self.params.decoder_size)
        result = self.fc(rnn_out)
        result = result.view(batch_size, seq_len, self.params.vocab_size)

        return result, final_state
