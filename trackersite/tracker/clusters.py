# -*- coding: utf-8 -*-

import tracker

class ClusterGroup(object):
    """ Group of ticket and transaction id sets for cluster assembly. """
    def __init__(self, tickets=None, transactions=None):
        self.tickets = tickets or set()
        self.transactions = transactions or set()
    
    def update(self, other_group):
        self.tickets.update(other_group.tickets)
        self.transactions.update(other_group.transactions)
    
    def has_tickets(self):
        return len(self.tickets) > 0
    
    def has_transactions(self):
        return len(self.transactions) > 0
    
    def has_items(self):
        return self.has_tickets() or self.has_transactions()

class ClusterUpdate(object):
    """ This holds all the context for cluster associations update. """
    
    def _reset_item_cluster(self, item):
        """
        Takes cluster-item (Ticket or Transaction), destroy its cluster, and queue
        all its members for update in big_todo (unless they already are in big_done).
        """
        try:
            cluster = item.cluster
        except tracker.models.Cluster.DoesNotExist:
            return # reference failure from earlier delete, we'll fix that later
        
        if cluster == None:
            return # done all right
        
        for ticket in cluster.ticket_set.all():
            if ticket.id not in self.big_done.tickets:
                self.big_todo.tickets.add(ticket.id)
        
        for transaction in cluster.transaction_set.all():
            if transaction.id not in self.big_done.transactions:
                self.big_todo.transactions.add(transaction.id)
        
        cluster.delete()
    
    def _make_one_cluster(self, seed):
        """ Make one cluster from seed item, updating the "big picture" """
        
        # this will be already 'processed' seed items
        precluster = ClusterGroup()
        
        while seed.has_items():
            if seed.has_tickets():
                ticket_id = seed.tickets.pop()
                ticket = tracker.models.Ticket.objects.get(id=ticket_id)
                for transaction in ticket.transaction_set.all():
                    if transaction.id not in precluster.transactions:
                        seed.transactions.add(transaction.id)
                        self.big_todo.transactions.discard(transaction.id)
                precluster.tickets.add(ticket_id)
            else: # there must be a transaction
                transaction_id = seed.transactions.pop()
                transaction = tracker.models.Transaction.objects.get(id=transaction_id)
                for ticket in transaction.tickets.all():
                    if ticket.id not in precluster.tickets:
                        seed.tickets.add(ticket.id)
                        self.big_todo.tickets.discard(ticket.id)
                precluster.transactions.add(transaction_id)
        
        # we have a completed cluster
        self.big_done.update(precluster) # our items are now considered done in the big scheme
        
        # clean up existing members
        for ticket in tracker.models.Ticket.objects.in_bulk(precluster.tickets).itervalues():
            self._reset_item_cluster(ticket)
        for transaction in tracker.models.Transaction.objects.in_bulk(precluster.transactions).itervalues():
            self._reset_item_cluster(transaction)
        
        if len(precluster.tickets) == 0:
            return # no tickets -> no cluster; leave transaction clusterless
        
        c = tracker.models.Cluster(id=min(precluster.tickets), more_tickets=(len(precluster.tickets)>1))
        c.save()
        for ti in tracker.models.Ticket.objects.in_bulk(precluster.tickets).itervalues():
            ti.cluster = c
            ti.save(cluster_update_only=True)
        for tr in tracker.models.Transaction.objects.in_bulk(precluster.transactions).itervalues():
            tr.cluster = c
            tr.save(cluster_update_only=True)
        c.update_status()

    @staticmethod
    def perform(ticket_ids=None, transaction_ids=None):
        """ Performs a propagating cluster update for mentioned tickets/transactions. """
        update = ClusterUpdate()
        update.big_todo = ClusterGroup(tickets=ticket_ids, transactions=transaction_ids)
        update.big_done = ClusterGroup()
        
        while update.big_todo.has_items():
            seed = ClusterGroup()
            if update.big_todo.has_tickets():
                seed.tickets.add(update.big_todo.tickets.pop())
            else: # transactions
                seed.transactions.add(update.big_todo.transactions.pop())
            update._make_one_cluster(seed)
    
    @staticmethod
    def refresh_all():
        ticket_ids = set([t.id for t in tracker.models.Ticket.objects.all().only('id')])
        transaction_ids = set([t.id for t in tracker.models.Transaction.objects.all().only('id')])
        ClusterUpdate.perform(ticket_ids, transaction_ids)
