import re
from sets import Set
import mailbox
#from mailbox import Maildir
#from mailbox import MaildirMessage

class Bayes(object):
    def __init__(self, th=.9):
        self.tokens = {}
        self.spam_count = 0
        self.ham_count = 0
        self.threshold = th
        # 2 classes - used for Laplacian smoothing
        self.classes = 2

    def _train_token(self, token, spam):
        if token in self.tokens:
            token = self.tokens[token]
        else:
            token = Token(token)
            self.tokens[token] = token
            
        if spam:
            token.spam_appear += 1
        else:
            token.ham_appear += 1

    def train_on_text(self, words, spam):
        for word in words:
            self._train_token(word, spam)
            #print word, self.tokens[word].spam_appear
        if spam:
            self.spam_count += 1
        else:
            self.ham_count += 1

    def _get_p(self, var):
        total = self.ham_count + self.spam_count
        if var == 'h':
            return self.ham_count / float(total)
        else:
            return self.spam_count / float(total)

    # returns p(s|w)
    # score p(s|w) based on 
    # p(s|w) = p(w|s) / p(w|s) + p(w|h)
    # s - spam, w - word, h - ham (non-spam)
    def _score_token(self, tk):
        if tk in self.tokens:
            return (self._p_token_given(tk, 'spam') * self._get_p('s')) / float((self._p_token_given(tk, 'spam') * self._get_p('s')) + (self._p_token_given(tk, 'ham') * self._get_p('h')))
        else: # word not seen before
            return 0.5

    # returns True for spam, False for ham
    def score_text(self, words):
        p_combined = 1
        not_p_combined = 1
        for word in words:
            score = self._score_token(word)
            #print word, score
            p_combined *= score
            not_p_combined *= (1-score)
        #print p_combined, not_p_combined
        p_spam = p_combined / float(p_combined + not_p_combined)
        print p_spam
        return self.threshold < p_spam

    def _p_token_given(self, token, given):
        tk = self.tokens[token]
        #print tk.token, tk.spam_appear, tk.ham_appear, self.spam_count, self.ham_count
        
        # +1 for laplacian smoothing
        if given == 'spam':
            appear = tk.spam_appear
            #count = self.spam_count
        if given == 'ham':
            appear = tk.ham_appear
            #count = self.ham_count

        count = tk.spam_appear + tk.ham_appear
        #print tk.token, given, (appear + 1) / float(count + self.classes)
        return (appear + 1) / float(count)# + self.classes)
     
    
class Token(object):
    def __init__(self, tk):
        self.token = tk
        # Laplace estimation
        self.spam_appear = 1
        self.ham_appear = 1

    def __hash__(self):
        return hash(self.token)
    
    def __eq__(self, other):
        return self.token == other

# opens file, reads text,
# and tokenizes, removes dupes of words
def read_file(filename):
    fp = open(filename, 'r')
    return(clean_text(fp.read()))

def clean_text(text):
    regex = re.compile('<.*>|[^a-zA-Z0-9_\s]|http://.*')
    return Set(regex.sub('', text).lower().split())

if __name__ == '__main__':
    b = Bayes()
    
    spam = read_file('spam1')
    spam1 = read_file('spam2')
    ham = read_file('ham1')
    

    b.train_on_text(spam, True)
    b.train_on_text(ham, False)                    
    b.train_on_text(spam1, True)

    test = read_file('spam2')
    
    print b.score_text(test)        
    print b.score_text(read_file('test1'))
    #print b.spam_count, b.ham_count
    #print b.tokens['spam'].spam_appear, b.tokens['spam'].ham_appear

    mbox = mailbox.Maildir('/home/lucas/Downloads/mail/', None)
    for key in mbox.keys():
        msg = mbox.get_message(key)
        payload = msg.as_string()
        b.train_on_text(clean_text(payload), False)
        
    spambox = mailbox.Maildir('/home/lucas/Downloads/spam/', None)
    for key in spambox.keys():
        msg = spambox.get_message(key)
        payload = msg.as_string()
        b.train_on_text(clean_text(payload), True)

    test = read_file('realspam1')
    print b.score_text(test)

    print b.score_text(read_file('notrealspam1'))
    #print b.score_text(read_file('realnonspam1'))

    print '++++++++++++++++++++++++++++++++++++++++++'
    c = 0
    for key, val in b.tokens.items():
        c += 1
        #if val.spam_appear / float(b.spam_count) > 0.9:
            #print val.token, val.spam_appear / float(b.spam_count)

    print 'count=',c
    print b.spam_count, b.ham_count
